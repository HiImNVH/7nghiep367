/**
 * Minimal wire types for contracts/openapi.yaml (T027).
 * Maintained manually; contract code generation is an M1 candidate.
 * UUIDs/date-times are strings. Numeric bounds and release gates are validated
 * by the API, not enforced by these TypeScript declarations.
 */
export type ArtifactKind = 'fixture' | 'pilot' | 'full';

export interface RequestHeaders {
  'X-Request-ID'?: string;
}

/** HTTP header values are strings; Retry-After represents whole seconds. */
export interface ResponseHeaders {
  'X-Request-ID': string;
  'Retry-After'?: string;
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  /** Artifact availability, independent of ModelInfo.demoReady. */
  modelReady: boolean;
  modelVersion?: string | null;
}

export interface ModelInfo {
  modelVersion: string;
  artifactKind: ArtifactKind;
  datasetVersion: string;
  featureSchemaVersion: string;
  extractorVersion: string;
  /** Actual supported meanings supplied by the API; do not hard-code them. */
  meanings: string[];
  acceptanceThreshold: number;
  macroF1: number | null;
  perMeaningRecall: Record<string, number> | null;
  evaluatedAt: string | null;
  demoReady: boolean;
}

/** Send as multipart FormData; do not JSON-encode the Blob. */
export interface PredictionRequest {
  clip: Blob;
}

/** Optional diagnostics must never determine acceptance in the client. */
export interface PredictionTimings {
  decode: number;
  extract: number;
  infer: number;
}

export interface PredictionQualityHints {
  handsDetectedRatio: number;
  frameCount: number;
}

export interface PredictionResponse {
  requestId: string;
  text: string;
  classLabel: string | null;
  confidence: number;
  accepted: boolean;
  modelVersion: string;
  processingTimeMs: number;
  timingsMs?: PredictionTimings;
  qualityHints?: PredictionQualityHints;
}

export type ErrorCode =
  | 'INVALID_REQUEST'
  | 'UNSUPPORTED_MEDIA_TYPE'
  | 'CLIP_TOO_LARGE'
  | 'CLIP_TOO_SHORT'
  | 'CLIP_TOO_LONG'
  | 'NO_PERSON_DETECTED'
  | 'INSUFFICIENT_LANDMARKS'
  | 'CLIP_DECODE_FAILED'
  | 'SERVICE_BUSY'
  | 'MODEL_NOT_READY'
  | 'PREDICTION_FAILED';

export interface ErrorEnvelope {
  code: ErrorCode;
  message: string;
  requestId: string;
}

export type PredictionErrorStatus = 400 | 413 | 415 | 422 | 500 | 503;
