import { StrictMode } from 'react';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { CameraRecorder } from '../../src/features/recognition/CameraRecorder';

class FakeRecorder extends EventTarget {
  static isTypeSupported = vi.fn(() => true);
  static latest: FakeRecorder;
  static data = 'camera bytes';
  state: RecordingState = 'inactive';
  mimeType = 'video/webm;codecs=vp8';
  constructor() { super(); FakeRecorder.latest = this; }
  start() { this.state = 'recording'; }
  stop() {
    this.state = 'inactive';
    queueMicrotask(() => {
      this.dispatchEvent(Object.assign(new Event('dataavailable'), {
        data: new Blob([FakeRecorder.data], { type: this.mimeType }),
      }));
      this.dispatchEvent(new Event('stop'));
    });
  }
}

let track: EventTarget & { stop: ReturnType<typeof vi.fn>; readyState: string };
let stream: MediaStream;
let getUserMedia: ReturnType<typeof vi.fn>;

beforeEach(() => {
  track = Object.assign(new EventTarget(), { stop: vi.fn(), readyState: 'live' });
  stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
  getUserMedia = vi.fn().mockResolvedValue(stream);
  vi.stubGlobal('isSecureContext', true);
  vi.stubGlobal('MediaRecorder', FakeRecorder);
  Object.defineProperty(navigator, 'mediaDevices', {
    configurable: true, value: { getUserMedia },
  });
  vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  FakeRecorder.isTypeSupported.mockReturnValue(true);
  FakeRecorder.data = 'camera bytes';
});

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

async function enableCamera() {
  await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
  await screen.findByRole('button', { name: 'Bắt đầu quay' });
}

describe('Camera permission and recording (T031 / T039)', () => {
  it('defaults to preview only without requiring MediaRecorder or recording automatically', async () => {
    vi.stubGlobal('MediaRecorder', undefined);
    const onClipReady = vi.fn();
    render(<CameraRecorder onClipReady={onClipReady} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    await screen.findByText('Camera đã sẵn sàng');
    expect((screen.getByLabelText('Hình ảnh xem trước từ camera') as HTMLVideoElement).srcObject).toBe(stream);
    expect(screen.queryByRole('button', { name: 'Bắt đầu quay' })).not.toBeInTheDocument();
    expect(screen.queryByRole('group', { name: 'Điều khiển ghi hình ký hiệu' })).not.toBeInTheDocument();
    expect(screen.queryByText(/rồi bắt đầu quay/)).not.toBeInTheDocument();
    expect(onClipReady).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Đặt lại' }));
    expect(track.stop).toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeEnabled();
  });

  it('requests camera only on user action, without audio, and attaches preview', async () => {
    render(<StrictMode><CameraRecorder recordingEnabled onClipReady={vi.fn()} /></StrictMode>);
    expect(getUserMedia).not.toHaveBeenCalled();
    await enableCamera();
    expect(getUserMedia).toHaveBeenCalledWith({
      audio: false, video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
    });
    expect((screen.getByLabelText('Hình ảnh xem trước từ camera') as HTMLVideoElement).srcObject).toBe(stream);
  });

  it('shows guidance for permission denied and lets the user retry', async () => {
    getUserMedia.mockRejectedValueOnce(new DOMException('denied', 'NotAllowedError'));
    render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Chưa có quyền sử dụng camera');
    await userEvent.click(screen.getByRole('button', { name: 'Thử lại' }));
    expect(await screen.findByRole('button', { name: 'Bắt đầu quay' })).toBeEnabled();
  });

  it('publishes final WebM only after explicit stop and final dataavailable', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    expect(onClipReady).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole('button', { name: 'Dừng quay' }));
    await waitFor(() => expect(onClipReady).toHaveBeenCalledOnce());
    expect(onClipReady.mock.calls[0]?.[0]).toMatchObject({ size: 12, type: 'video/webm;codecs=vp8' });
  });

  it('discards cancelled recording even when final events arrive later', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await userEvent.click(screen.getByRole('button', { name: 'Hủy đoạn quay' }));
    expect(onClipReady).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Bắt đầu quay' })).toBeEnabled();
  });

  it('stops tracks and clears preview on unmount', async () => {
    const { unmount } = render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await enableCamera();
    const video = screen.getByLabelText('Hình ảnh xem trước từ camera') as HTMLVideoElement;
    unmount();
    expect(track.stop).toHaveBeenCalled();
    expect(video.srcObject).toBeNull();
  });

  it('releases a stream returned after permission request was cancelled', async () => {
    let resolve!: (value: MediaStream) => void;
    getUserMedia.mockReturnValue(new Promise<MediaStream>((done) => { resolve = done; }));
    render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    await userEvent.click(screen.getByRole('button', { name: 'Hủy yêu cầu' }));
    await act(async () => resolve(stream));
    expect(track.stop).toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeEnabled();
  });

  it('discards clip and gives guidance when track disconnects mid-recording', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await act(async () => { track.dispatchEvent(new Event('ended')); });
    expect(screen.getByRole('alert')).toHaveTextContent('Camera đã mất kết nối');
    expect(onClipReady).not.toHaveBeenCalled();
  });

  it('rejects unsupported WebM before asking for camera', async () => {
    FakeRecorder.isTypeSupported.mockReturnValue(false);
    render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Trình duyệt chưa hỗ trợ ghi hình');
    expect(getUserMedia).not.toHaveBeenCalled();
  });

  it('cleans up when preview playback fails', async () => {
    vi.mocked(HTMLMediaElement.prototype.play).mockRejectedValue(new Error('play failed'));
    render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    expect(await screen.findByRole('alert')).toBeVisible();
    expect(track.stop).toHaveBeenCalled();
  });

  it('discards recording on recorder error', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await act(async () => { FakeRecorder.latest.dispatchEvent(new Event('error')); });
    expect(screen.getByRole('alert')).toHaveTextContent('Không ghi được đoạn camera');
    expect(onClipReady).not.toHaveBeenCalled();
  });

  it('does not publish an unexpectedly stopped recording', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await act(async () => { FakeRecorder.latest.stop(); });
    expect(screen.getByRole('alert')).toHaveTextContent('Không ghi được đoạn camera');
    expect(onClipReady).not.toHaveBeenCalled();
  });

  it('does not publish an empty recording', async () => {
    FakeRecorder.data = '';
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await userEvent.click(screen.getByRole('button', { name: 'Dừng quay' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Không ghi được đoạn camera');
    expect(onClipReady).not.toHaveBeenCalled();
  });

  it('stops a stream that resolves after StrictMode component unmounts', async () => {
    let resolve!: (value: MediaStream) => void;
    getUserMedia.mockReturnValue(new Promise<MediaStream>((done) => { resolve = done; }));
    const { unmount } = render(<StrictMode><CameraRecorder recordingEnabled onClipReady={vi.fn()} /></StrictMode>);
    await userEvent.click(screen.getByRole('button', { name: 'Bật camera' }));
    unmount();
    await act(async () => resolve(stream));
    expect(track.stop).toHaveBeenCalledOnce();
  });

  it('reset stops camera, clears clip overlay and restores the initial controls', async () => {
    render(<CameraRecorder recordingEnabled onClipReady={vi.fn()} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await userEvent.click(screen.getByRole('button', { name: 'Dừng quay' }));
    expect(await screen.findByRole('heading', { name: 'Đã quay xong' })).toBeVisible();
    await userEvent.click(screen.getByRole('button', { name: 'Đặt lại' }));
    expect(track.stop).toHaveBeenCalled();
    expect(screen.queryByRole('heading', { name: 'Đã quay xong' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Hiện kết quả' })).not.toBeInTheDocument();
    expect(screen.queryByText('Xin chào!')).not.toBeInTheDocument();
  });

  it('reset during recording discards final events and releases tracks', async () => {
    const onClipReady = vi.fn();
    render(<CameraRecorder recordingEnabled onClipReady={onClipReady} />);
    await enableCamera();
    await userEvent.click(screen.getByRole('button', { name: 'Bắt đầu quay' }));
    await userEvent.click(screen.getByRole('button', { name: 'Đặt lại' }));
    expect(track.stop).toHaveBeenCalled();
    expect(onClipReady).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Bật camera' })).toBeEnabled();
  });

});

