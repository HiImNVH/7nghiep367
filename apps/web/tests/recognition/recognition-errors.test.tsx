import { StrictMode } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../src/App';
import { InferenceApiError, type InferenceApi } from '../../src/services/inferenceApi';
import { model, accepted, requestId } from '../fixtures/inference';
import type { PredictionResponse } from '../../src/types/inference-api';
import { createInferenceApi } from '../../src/services/inferenceApi';

class Recorder extends EventTarget {
  static instances = 0;
  static isTypeSupported() { return true; }
  state: RecordingState = 'inactive';
  mimeType = 'video/webm';
  constructor() { super(); Recorder.instances++; }
  start() { this.state = 'recording'; }
  stop() {
    this.state = 'inactive';
    queueMicrotask(() => {
      this.dispatchEvent(Object.assign(new Event('dataavailable'), { data: new Blob(['clip'], { type: 'video/webm' }) }));
      this.dispatchEvent(new Event('stop'));
    });
  }
}
let stopTrack: ReturnType<typeof vi.fn>;
let getUserMedia: ReturnType<typeof vi.fn>;
beforeEach(() => {
  Recorder.instances = 0;
  stopTrack = vi.fn();
  const track = Object.assign(new EventTarget(), { stop: stopTrack, readyState: 'live' });
  getUserMedia = vi.fn().mockResolvedValue({ getTracks: () => [track], getVideoTracks: () => [track] });
  Object.defineProperty(navigator, 'mediaDevices', { configurable: true, value: { getUserMedia } });
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', Recorder);
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

function mockApi(): InferenceApi {
  return {
    health: vi.fn().mockResolvedValue({ status: 'ok', modelReady: true }),
    modelInfo: vi.fn().mockResolvedValue(model),
    predict: vi.fn().mockResolvedValue(accepted),
  };
}
async function prepareCapture() {
  await screen.findByText(/Kết quả tạo sẵn/);
  await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  const recognize = await screen.findByRole('button', { name: 'Nhận diện' });
  expect(Recorder.instances).toBe(0);
  expect(screen.queryByRole('button', { name: 'Bắt đầu quay' })).not.toBeInTheDocument();
  await userEvent.click(recognize);
}
async function finishCapture() {
  await userEvent.click(screen.getByRole('button', { name: 'Kết thúc' }));
  await screen.findByRole('button', { name: 'Gửi nhận diện' });
}

describe('Full frontend recognition flow and recovery (T031 / T043 / T046 / T051–T053)', () => {
  it('captures only on explicit recognition, sends only after explicit submit, renders accepted result', async () => {
    const api = mockApi();
    render(<StrictMode><App api={api} /></StrictMode>);
    await prepareCapture();
    expect(api.predict).not.toHaveBeenCalled();
    await finishCapture();
    expect(api.predict).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    expect(await screen.findByRole('heading', { name: 'Xin chào' })).toHaveFocus();
    expect(screen.getByText(/94/)).toBeVisible();
    expect(screen.getByText(/không thay thế phiên dịch viên/, { selector: '.result-disclaimer' })).toBeVisible();
    expect(api.predict).toHaveBeenCalledOnce();
  });
  it('shows rejected outcome and retries without retaining a clip or replaying an upload', async () => {
    const api = mockApi();
    vi.mocked(api.predict).mockResolvedValue({ ...accepted, accepted: false, text: 'Do not show this suggestion', classLabel: null });
    render(<App api={api} />);
    await prepareCapture(); await finishCapture();
    await userEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    expect(await screen.findByRole('heading', { name: 'Không nhận diện được' })).toBeVisible();
    expect(screen.queryByText('Do not show this suggestion')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('button', { name: 'Nhận diện' })).toBeEnabled();
    expect(api.predict).toHaveBeenCalledOnce();
  });
  it('cancels before final recorder event without uploading', async () => {
    const api = mockApi(); render(<App api={api} />);
    await prepareCapture();
    await userEvent.click(screen.getByRole('button', { name: 'Hủy đoạn quay' }));
    expect(screen.queryByRole('button', { name: 'Gửi nhận diện' })).not.toBeInTheDocument();
    expect(api.predict).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Nhận diện' })).toHaveFocus();
  });
  it.each(['cancel', 'reset', 'unmount'] as const)('aborts on %s and ignores late results even from an adapter that ignores abort', async action => {
    const api = mockApi();
    let resolve!: (result: PredictionResponse) => void;
    let signal: AbortSignal | undefined;
    vi.mocked(api.predict).mockImplementation((_clip, options) => {
      signal = options?.signal;
      return new Promise(done => { resolve = done; });
    });
    const { unmount } = render(<App api={api} />);
    await prepareCapture(); await finishCapture();
    const send = screen.getByRole('button', { name: 'Gửi nhận diện' });
    await userEvent.dblClick(send);
    expect(api.predict).toHaveBeenCalledOnce();
    if (action === 'unmount') unmount();
    else await userEvent.click(screen.getByRole('button', { name: action === 'reset' ? 'Đặt lại' : 'Hủy yêu cầu' }));
    expect(signal?.aborted).toBe(true);
    await act(async () => resolve(accepted));
    expect(screen.queryByRole('heading', { name: 'Xin chào' })).not.toBeInTheDocument();
    if (action === 'reset') expect(stopTrack).toHaveBeenCalled();
  });
  it.each(['SERVICE_BUSY', 'CLIP_DECODE_FAILED', 'MODEL_NOT_READY', 'PREDICTION_FAILED', 'network'] as const)('presents %s in Vietnamese and recovers by retry', async code => {
    const api = mockApi();
    vi.mocked(api.predict).mockRejectedValue(new InferenceApiError(code, requestId, code === 'SERVICE_BUSY' ? 2 : undefined));
    render(<App api={api} />); await prepareCapture(); await finishCapture();
    await userEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(code === 'SERVICE_BUSY' ? 'Hệ thống đang bận' : code === 'CLIP_DECODE_FAILED' ? 'Không đọc được đoạn ghi hình' : code === 'MODEL_NOT_READY' ? 'Dịch vụ nhận diện chưa sẵn sàng' : code === 'network' ? 'Không kết nối được dịch vụ' : 'Không thể hoàn tất nhận diện');
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    await waitFor(() => expect(screen.getByRole('button', { name: 'Nhận diện' })).toBeEnabled());
  });
  it('shows model-info failure, then loads actual supported scope when retry succeeds', async () => {
    const api = mockApi(); vi.mocked(api.modelInfo).mockRejectedValueOnce(new InferenceApiError('MODEL_NOT_READY'));
    render(<App api={api} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Dịch vụ nhận diện chưa sẵn sàng');
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByText(/Kết quả tạo sẵn/)).toBeVisible();
  });
  it('keeps denied camera permission distinct from service readiness', async () => {
    getUserMedia.mockRejectedValue(new DOMException('denied', 'NotAllowedError'));
    const api = mockApi(); render(<App api={api} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Chưa có quyền sử dụng camera');
    expect(api.predict).not.toHaveBeenCalled();
  });
  it('exposes a real API timeout as a recoverable model-info error', async () => {
    const api = createInferenceApi({ timeoutMs: 20, fetcher: () => new Promise(() => {}) });
    render(<App api={api} />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Chờ kết quả quá lâu');
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeEnabled();
  });
  it('refuses to attribute results to stale model-info after an artifact swap', async () => {
    const api = mockApi(); vi.mocked(api.predict).mockResolvedValue({ ...accepted, modelVersion: 'new-version' });
    render(<App api={api} />); await prepareCapture(); await finishCapture();
    await userEvent.click(screen.getByRole('button', { name: 'Gửi nhận diện' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Dịch vụ nhận diện chưa sẵn sàng');
    expect(screen.queryByRole('heading', { name: 'Xin chào' })).not.toBeInTheDocument();
  });
  it('stops capture at the configured safety cap without automatically uploading', async () => {
    vi.stubEnv('VITE_MAX_CAPTURE_MS', '1000');
    const api = mockApi(); render(<App api={api} />);
    await prepareCapture();
    await waitFor(() => expect(screen.getByRole('button', { name: 'Gửi nhận diện' })).toBeVisible(), { timeout: 1800 });
    expect(api.predict).not.toHaveBeenCalled();
  });
});

