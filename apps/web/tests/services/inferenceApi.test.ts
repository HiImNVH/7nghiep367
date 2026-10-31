// @vitest-environment node
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';
import { delay, http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { createInferenceApi } from '../../src/services/inferenceApi';
import { accepted, model, requestId } from '../fixtures/inference';

const origin = 'http://127.0.0.1:8000';
const server = setupServer();
beforeAll(() => server.listen({ onUnhandledFrame: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
const api = createInferenceApi({ baseUrl: origin, timeoutMs: 200 });

describe('OpenAPI transport (T040)', () => {
  it('reads nullable fixture metrics and sends correlation UUID', async () => {
    server.use(http.get(`${origin}/api/v1/model-info`, ({ request }) => {
      expect(request.headers.get('X-Request-ID')).toMatch(/^[\da-f-]{36}$/i);
      return HttpResponse.json(model);
    }));
    expect(await api.modelInfo()).toEqual(model);
  });
  it('sends multipart clip without manually setting Content-Type, reads the response ID, tolerates missing diagnostics', async () => {
    server.use(http.post(`${origin}/api/v1/predictions`, async ({ request }) => {
      const form = await request.formData();
      expect((form.get('clip') as File).name).toBe('capture.webm');
      expect(request.headers.get('Content-Type')).toMatch(/multipart\/form-data; boundary=/);
      return HttpResponse.json(accepted, { headers: { 'X-Request-ID': requestId } });
    }));
    expect(await api.predict(new Blob(['video'], { type: 'video/webm' }))).toEqual(accepted);
  });
  it.each([
    [400, 'INVALID_REQUEST'], [413, 'CLIP_TOO_LARGE'], [415, 'UNSUPPORTED_MEDIA_TYPE'],
    [422, 'CLIP_DECODE_FAILED'], [503, 'SERVICE_BUSY'], [503, 'MODEL_NOT_READY'], [500, 'PREDICTION_FAILED'],
  ] as const)('maps HTTP %s %s without exposing raw server text', async (status, code) => {
    server.use(http.post(`${origin}/api/v1/predictions`, () => HttpResponse.json(
      { code, requestId, message: 'internal secret traceback' },
      { status, headers: { 'Retry-After': '2', 'X-Request-ID': requestId } },
    )));
    await expect(api.predict(new Blob(['clip']))).rejects.toMatchObject({ code, requestId, retryAfter: 2 });
  });
  it('rejects malformed success and mismatched response header/body IDs', async () => {
    server.use(http.post(`${origin}/api/v1/predictions`, () => HttpResponse.json({ ...accepted, confidence: 2 })));
    await expect(api.predict(new Blob(['clip']))).rejects.toMatchObject({ code: 'invalidResponse' });
    server.use(http.post(`${origin}/api/v1/predictions`, () => HttpResponse.json(accepted, { headers: { 'X-Request-ID': 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa' } })));
    await expect(api.predict(new Blob(['clip']))).rejects.toMatchObject({ code: 'invalidResponse' });
  });
  it('distinguishes timeout from caller cancellation', async () => {
    server.use(http.get(`${origin}/api/v1/model-info`, async () => { await delay(80); return HttpResponse.json(model); }));
    await expect(createInferenceApi({ baseUrl: origin, timeoutMs: 10 }).modelInfo()).rejects.toMatchObject({ code: 'timeout' });
    const controller = new AbortController();
    const pending = api.modelInfo({ signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toMatchObject({ code: 'cancelled' });
  });
  it('maps a network failure', async () => {
    server.use(http.get(`${origin}/api/v1/model-info`, () => HttpResponse.error()));
    await expect(api.modelInfo()).rejects.toMatchObject({ code: 'network' });
  });
  it.each([502, 504])('maps a plain HTTP %s gateway failure to an unavailable service', async status => {
    server.use(http.get(`${origin}/api/v1/model-info`, () => new HttpResponse('', { status })));
    await expect(api.modelInfo()).rejects.toMatchObject({ code: 'network' });
  });
  it('still rejects a successful HTML response as invalid', async () => {
    server.use(http.get(`${origin}/api/v1/model-info`, () => HttpResponse.html('<html>Wrong service</html>')));
    await expect(api.modelInfo()).rejects.toMatchObject({ code: 'invalidResponse' });
  });
});
