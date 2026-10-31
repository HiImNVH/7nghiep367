import { apiErrors } from '../content/vi';
import type { ErrorCode, ErrorEnvelope, HealthResponse, ModelInfo, PredictionResponse } from '../types/inference-api';

export type ClientErrorCode = ErrorCode | 'network' | 'timeout' | 'cancelled' | 'invalidResponse';
export class InferenceApiError extends Error {
  constructor(
    readonly code: ClientErrorCode,
    readonly requestId?: string,
    readonly retryAfter?: number,
  ) { super(code); this.name = 'InferenceApiError'; }
}

const object = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === 'string';
const unit = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1;
const milliseconds = (v: unknown): v is number => Number.isInteger(v) && Number(v) >= 0;
const uuid = (v: unknown): v is string => text(v) && /^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}-[\da-f]{12}$/i.test(v);
function isModelInfo(v: unknown): v is ModelInfo {
  return object(v) && ['modelVersion', 'datasetVersion', 'featureSchemaVersion', 'extractorVersion'].every(k => text(v[k]))
    && ['fixture', 'pilot', 'full'].includes(String(v.artifactKind))
    && Array.isArray(v.meanings) && v.meanings.length >= 1 && v.meanings.length <= 10 && v.meanings.every(text)
    && unit(v.acceptanceThreshold) && (v.macroF1 === null || unit(v.macroF1))
    && (v.perMeaningRecall === null || (object(v.perMeaningRecall) && Object.values(v.perMeaningRecall).every(unit)))
    && (v.evaluatedAt === null || (text(v.evaluatedAt) && Number.isFinite(Date.parse(v.evaluatedAt))))
    && typeof v.demoReady === 'boolean';
}
function isPrediction(v: unknown): v is PredictionResponse {
  return object(v) && uuid(v.requestId) && text(v.text) && (v.classLabel === null || text(v.classLabel))
    && unit(v.confidence) && typeof v.accepted === 'boolean' && text(v.modelVersion) && milliseconds(v.processingTimeMs)
    && (v.timingsMs === undefined || (object(v.timingsMs) && ['decode', 'extract', 'infer'].every(k => milliseconds((v.timingsMs as Record<string, unknown>)[k]))))
    && (v.qualityHints === undefined || (object(v.qualityHints) && unit(v.qualityHints.handsDetectedRatio) && Number.isInteger(v.qualityHints.frameCount) && Number(v.qualityHints.frameCount) >= 1));
}
function isHealth(v: unknown): v is HealthResponse {
  return object(v) && ['ok', 'degraded'].includes(String(v.status)) && typeof v.modelReady === 'boolean'
    && (v.modelVersion === undefined || v.modelVersion === null || text(v.modelVersion));
}
function isError(v: unknown): v is ErrorEnvelope {
  return object(v) && text(v.code) && Object.hasOwn(apiErrors, v.code) && uuid(v.requestId) && text(v.message);
}

export interface ApiOptions { signal?: AbortSignal }
export interface InferenceApi {
  health(options?: ApiOptions): Promise<HealthResponse>;
  modelInfo(options?: ApiOptions): Promise<ModelInfo>;
  predict(clip: Blob, options?: ApiOptions): Promise<PredictionResponse>;
}
export function createInferenceApi({ baseUrl = '', timeoutMs = 10_000, fetcher }: {
  baseUrl?: string; timeoutMs?: number; fetcher?: typeof fetch;
} = {}): InferenceApi {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error('Invalid API timeout');
  const base = baseUrl.replace(/\/$/, '');
  async function request<T>(path: string, validate: (body: unknown) => body is T, options: ApiOptions = {}, clip?: Blob): Promise<T> {
    const controller = new AbortController();
    let timedOut = false;
    const sentId = crypto.randomUUID();
    let effectiveId: string = sentId;
    const abort = () => controller.abort();
    const external = options.signal;
    external?.addEventListener('abort', abort, { once: true });
    if (external?.aborted) controller.abort();
    let rejectAbort: (reason: InferenceApiError) => void = () => {};
    const aborted = new Promise<never>((_, reject) => { rejectAbort = reject; });
    const onAbort = () => rejectAbort(new InferenceApiError(timedOut ? 'timeout' : 'cancelled', effectiveId));
    controller.signal.addEventListener('abort', onAbort, { once: true });
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
    try {
      if (controller.signal.aborted) throw new InferenceApiError('cancelled', sentId);
      const operation = async () => {
        const form = clip === undefined ? undefined : new FormData();
        if (form && clip) form.append('clip', clip, 'capture.webm');
        const response = await (fetcher ?? fetch)(`${base}${path}`, {
          method: form ? 'POST' : 'GET', headers: { Accept: 'application/json', 'X-Request-ID': sentId },
          ...(form ? { body: form } : {}), signal: controller.signal, cache: 'no-store',
        });
        const headerId = response.headers.get('X-Request-ID');
        if (headerId !== null) {
          if (!uuid(headerId)) throw new InferenceApiError('invalidResponse', sentId);
          effectiveId = headerId;
        }
        let body: unknown;
        // A disconnected upstream can produce an empty/text proxy response.
        // Preserve contract errors when present, but classify gateway failures
        // as unavailable connectivity rather than malformed model results.
        const responseError = response.status === 502 || response.status === 504 ? 'network' : 'invalidResponse';
        try { body = await response.json(); } catch { throw new InferenceApiError(responseError, effectiveId); }
        if (headerId && object(body) && 'requestId' in body && body.requestId !== headerId) throw new InferenceApiError('invalidResponse', effectiveId);
        if (!response.ok) {
          if (!isError(body)) throw new InferenceApiError(responseError, effectiveId);
          const retry = response.headers.get('Retry-After');
          const retryAfter = retry && /^[1-9]\d*$/.test(retry) && Number.isSafeInteger(Number(retry)) ? Number(retry) : undefined;
          // Never display the server's message: stable Vietnamese catalog only.
          throw new InferenceApiError(body.code, body.requestId, retryAfter);
        }
        if (!validate(body)) throw new InferenceApiError('invalidResponse', effectiveId);
        return body;
      };
      return await Promise.race([operation(), aborted]);
    } catch (cause) {
      if (cause instanceof InferenceApiError) throw cause;
      if (controller.signal.aborted) throw new InferenceApiError(timedOut ? 'timeout' : 'cancelled', effectiveId);
      throw new InferenceApiError('network', effectiveId);
    } finally {
      clearTimeout(timer);
      external?.removeEventListener('abort', abort);
      controller.signal.removeEventListener('abort', onAbort);
    }
  }
  return {
    health: options => request('/api/v1/health', isHealth, options),
    modelInfo: options => request('/api/v1/model-info', isModelInfo, options),
    predict: (clip, options) => request('/api/v1/predictions', isPrediction, options, clip),
  };
}

export const inferenceApi = createInferenceApi({
  baseUrl: import.meta.env.VITE_API_BASE_URL || '',
  timeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS || 10_000),
});
