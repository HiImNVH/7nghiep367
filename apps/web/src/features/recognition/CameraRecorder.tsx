import { useCallback, useEffect, useRef, useState } from 'react';
import { cameraErrors, vi, type ErrorCopy } from '../../content/vi';
import { FramingGuide } from './FramingGuide';
import { UiIcon } from '../../components/UiIcon';
import { CameraHelp } from '../../components/CameraHelp';
import type { RecognitionController } from './useRecognition';
import { RecognitionResult } from './RecognitionResult';
import { RecognitionError } from './RecognitionError';
import { ModelNotice } from './ModelNotice';

type CameraState = 'idle' | 'permission' | 'ready' | 'recording' | 'stopping' | 'error';

interface CameraRecorderProps {
  /** Manual capture is opt-in; the current app only shows camera preview. */
  recordingEnabled?: boolean;
  recognition?: RecognitionController;
  onClipReady?: (clip: Blob) => void;
  onClipDiscard?: () => void;
}

const webmTypes = ['video/webm;codecs=vp8', 'video/webm;codecs=vp9', 'video/webm'];

export function CameraRecorder({ onClipReady, onClipDiscard, recordingEnabled = false, recognition }: CameraRecorderProps) {
  const [state, setState] = useState<CameraState>('idle');
  const [error, setError] = useState<ErrorCopy | null>(null);
  const [status, setStatus] = useState<string>(vi.status.idle);
  const [clip, setClip] = useState<Blob | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const attachedPreview = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const stopRequested = useRef<MediaRecorder | null>(null);
  const disposeRecording = useRef<() => void>(() => {});
  const disposeStreamEvents = useRef<() => void>(() => {});
  const generation = useRef(0);
  const requesting = useRef(false);
  const mimeRef = useRef('');
  const captureTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const finalizeTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const cancelRecognition = recognition?.cancel;

  // Invalidate callbacks before stopping resources: final recorder events can be late.
  const discardRecording = useCallback(() => {
    clearTimeout(captureTimer.current);
    clearTimeout(finalizeTimer.current);
    const recorder = recorderRef.current;
    recorderRef.current = null;
    stopRequested.current = null;
    disposeRecording.current();
    disposeRecording.current = () => {};
    if (recorder && recorder.state !== 'inactive') {
      try { recorder.stop(); } catch { /* Device may already have stopped. */ }
    }
  }, []);

  const releaseCamera = useCallback(() => {
    generation.current += 1;
    requesting.current = false;
    discardRecording();
    disposeStreamEvents.current();
    disposeStreamEvents.current = () => {};
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (attachedPreview.current) attachedPreview.current.srcObject = null;
    attachedPreview.current = null;
  }, [discardRecording]);

  useEffect(() => {
    const onPageHide = () => {
      releaseCamera();
      onClipDiscard?.();
      cancelRecognition?.();
      setClip(null);
      setState('idle');
      setStatus(vi.status.idle);
    };
    window.addEventListener('pagehide', onPageHide);
    return () => {
      window.removeEventListener('pagehide', onPageHide);
      releaseCamera();
    };
  }, [releaseCamera, onClipDiscard, cancelRecognition]);

  function fail(copy: ErrorCopy) {
    releaseCamera();
    onClipDiscard?.();
    cancelRecognition?.();
    setClip(null);
    setError(copy);
    setStatus(copy.title);
    setState('error');
  }

  async function enableCamera() {
    if (requesting.current) return;
    setError(null);
    if (!window.isSecureContext) { fail(cameraErrors.insecureContext); return; }
    const captureEnabled = recordingEnabled || !!recognition;
    if (!navigator.mediaDevices?.getUserMedia || (captureEnabled && typeof MediaRecorder === 'undefined')) {
      fail(cameraErrors.unsupported); return;
    }
    const mimeType = captureEnabled ? webmTypes.find((type) => MediaRecorder.isTypeSupported(type)) : '';
    if (captureEnabled && !mimeType) { fail(cameraErrors.unsupported); return; }
    releaseCamera();
    const session = generation.current;
    requesting.current = true;
    setState('permission');
    setStatus(vi.status.requestingPermission);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 30 } },
      });
      if (session !== generation.current) {
        stream.getTracks().forEach((track) => track.stop());
        return;
      }
      streamRef.current = stream;
      const tracks = stream.getVideoTracks();
      if (!tracks.length || tracks.some((track) => track.readyState !== 'live')) {
        fail(cameraErrors.disconnected); return;
      }
      const onEnded = () => {
        if (generation.current === session) fail(cameraErrors.disconnected);
      };
      tracks.forEach((track) => track.addEventListener('ended', onEnded));
      disposeStreamEvents.current = () => tracks.forEach((track) => track.removeEventListener('ended', onEnded));
      const video = videoRef.current;
      if (!video) { releaseCamera(); return; }
      video.srcObject = stream;
      attachedPreview.current = video;
      await video.play();
      if (session !== generation.current) return;
      requesting.current = false;
      mimeRef.current = mimeType || '';
      setState('ready');
      setStatus(vi.status.ready);
    } catch (cause) {
      if (session !== generation.current) return;
      const name = typeof cause === 'object' && cause !== null && 'name' in cause && typeof cause.name === 'string'
        ? cause.name : '';
      const copy = Object.hasOwn(cameraErrors, name)
        ? cameraErrors[name as keyof typeof cameraErrors] : cameraErrors.unknown;
      fail(copy);
    }
  }

  function startRecording() {
    if (!recordingEnabled && !recognition) return;
    if (!streamRef.current || recorderRef.current || state !== 'ready') return;
    if (recognition && !recognition.beginCapture()) return;
    onClipDiscard?.();
    setClip(null);
    const chunks: Blob[] = [];
    try {
      const recorder = new MediaRecorder(streamRef.current, { mimeType: mimeRef.current });
      recorderRef.current = recorder;
      const isCurrent = () => recorderRef.current === recorder;
      const onData = (event: BlobEvent) => {
        if (isCurrent() && event.data.size > 0) chunks.push(event.data);
      };
      const onStop = () => {
        if (!isCurrent()) return;
        clearTimeout(captureTimer.current);
        clearTimeout(finalizeTimer.current);
        if (stopRequested.current !== recorder) { fail(cameraErrors.recordingFailed); return; }
        const clip = new Blob(chunks, { type: recorder.mimeType || mimeRef.current });
        recorderRef.current = null;
        stopRequested.current = null;
        disposeRecording.current();
        disposeRecording.current = () => {};
        if (!clip.size) { fail(cameraErrors.recordingFailed); return; }
        setState('ready');
        setStatus(vi.status.recorded);
        if (recognition) recognition.captureReady(clip);
        else setClip(clip);
        onClipReady?.(clip);
      };
      const onError = () => { if (isCurrent()) fail(cameraErrors.recordingFailed); };
      recorder.addEventListener('dataavailable', onData);
      recorder.addEventListener('stop', onStop);
      recorder.addEventListener('error', onError);
      disposeRecording.current = () => {
        chunks.length = 0;
        recorder.removeEventListener('dataavailable', onData);
        recorder.removeEventListener('stop', onStop);
        recorder.removeEventListener('error', onError);
      };
      recorder.start();
      setState('recording');
      setStatus(vi.status.recording);
      if (recognition) {
        const configuredMax = Number(import.meta.env.VITE_MAX_CAPTURE_MS || 5000);
        const maximum = Number.isFinite(configuredMax) && configuredMax >= 1000 && configuredMax <= 30000 ? configuredMax : 5000;
        captureTimer.current = setTimeout(() => { if (isCurrent()) stopRecording(); }, maximum);
      }
    } catch { fail(cameraErrors.recordingFailed); }
  }

  function stopRecording() {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state !== 'recording') return;
    clearTimeout(captureTimer.current);
    stopRequested.current = recorder;
    setState('stopping');
    setStatus('Đang hoàn tất đoạn ghi hình…');
    try {
      recorder.stop();
      finalizeTimer.current = setTimeout(() => { if (recorderRef.current === recorder) fail(cameraErrors.recordingFailed); }, 3000);
    } catch { fail(cameraErrors.recordingFailed); }
  }

  function cancel() {
    cancelRecognition?.();
    onClipDiscard?.();
    setClip(null);
    if (state === 'permission') {
      releaseCamera();
      setState('idle');
    } else {
      discardRecording();
      setState('ready');
    }
    setStatus(vi.status.cancelled);
  }

  function reset() {
    cancelRecognition?.();
    releaseCamera();
    onClipDiscard?.();
    setClip(null);
    setError(null);
    setState('idle');
    setStatus(vi.status.idle);
  }

  const isCapturing = state === 'recording' || state === 'stopping';
  const hasCamera = state === 'ready' || isCapturing;
  const attempt = recognition?.attempt;
  const captured = attempt?.phase === 'captured';
  const submitting = attempt?.phase === 'submitting';
  const outcome = attempt?.phase === 'result' || attempt?.phase === 'error' || recognition?.modelStatus === 'error';
  const canRecognize = recognition?.modelStatus === 'ready' && attempt?.phase === 'idle';
  const phase = attempt?.phase;
  const modelStatus = recognition?.modelStatus;
  const previousView = useRef({ state, phase, modelStatus });
  useEffect(() => {
    const previous = previousView.current;
    const cameraBecameUsable = (state === 'ready' || state === 'idle' || state === 'error') && previous.state !== state;
    const attemptBecameUsable = (phase === 'idle' || phase === 'captured') && previous.phase !== phase;
    const scopeBecameUsable = state === 'ready' && modelStatus === 'ready' && previous.modelStatus !== modelStatus;
    if (cameraBecameUsable || attemptBecameUsable || scopeBecameUsable) {
      const action = panelRef.current?.querySelector<HTMLButtonElement>('.capture-controls button:not([disabled])')
        ?? panelRef.current?.querySelector<HTMLButtonElement>('.reset-button');
      action?.focus();
    }
    previousView.current = { state, phase, modelStatus };
  }, [state, phase, modelStatus]);
  const badge = state === 'error' ? 'Camera gặp lỗi'
    : state === 'permission' ? 'Đang chờ quyền camera'
    : state === 'recording' ? 'Đang quay ký hiệu'
    : state === 'stopping' ? 'Đang hoàn tất'
    : submitting ? 'Đang xử lý'
    : attempt?.phase === 'result' ? (attempt.result.accepted ? 'Đã nhận diện' : 'Chưa nhận diện được')
    : attempt?.phase === 'error' ? 'Nhận diện gặp lỗi'
    : captured || clip ? 'Đã quay xong'
    : hasCamera ? 'Camera đã sẵn sàng' : 'Camera chưa bật';
  const instruction = state === 'error' ? 'Mình thử lại nhé.'
    : state === 'permission' ? 'Chỉ một bước nữa thôi.'
    : submitting ? 'Đang nhận diện ký hiệu…'
    : attempt?.phase === 'result' ? 'Kết quả nhận diện của bạn.'
    : attempt?.phase === 'error' ? 'Chưa thể hoàn tất nhận diện.'
    : isCapturing ? 'Hãy thực hiện ký hiệu của bạn.'
    : captured || clip ? 'Đã ghi lại cử chỉ của bạn.'
    : hasCamera ? 'Bạn đã sẵn sàng.' : 'Đưa cử chỉ thành lời.';
  const description = state === 'permission' ? 'Cho phép sử dụng camera trong thông báo của trình duyệt.'
    : submitting ? 'Bạn có thể hủy yêu cầu nếu không muốn tiếp tục.'
    : attempt?.phase === 'result' || attempt?.phase === 'error' ? 'Bạn có thể thử lại với một ký hiệu mới.'
    : isCapturing ? (recognition ? 'Nhấn Kết thúc khi xong. Đoạn quay tự kết thúc ở giới hạn thời lượng.' : 'Khi thực hiện xong một ký hiệu, hãy nhấn dừng quay.')
    : captured ? 'Chọn Gửi nhận diện để phân tích hoặc hủy đoạn vừa quay.'
    : clip ? 'Bạn có thể quay lại nếu muốn thực hiện rõ hơn.'
    : hasCamera ? (recordingEnabled ? 'Giữ khuôn mặt và hai tay trong khung hình, rồi bắt đầu quay.' : 'Giữ khuôn mặt và hai tay trong khung hình.')
    : 'Một ký hiệu mỗi lần. Bắt đầu khi bạn thấy thoải mái.';

  return (
    <section className="camera-experience" aria-label="Nhận diện ký hiệu bằng camera">
      <div ref={panelRef} className={`camera-panel ${hasCamera ? 'camera-on' : ''} ${clip || captured ? 'clip-ready' : ''} ${outcome ? 'has-recognition-outcome' : ''}`}>
        <video ref={videoRef} autoPlay muted playsInline aria-label={vi.a11y.cameraPreview} />
        <div className="camera-tint" />
        <div className="panel-topbar">
          <div className="brand"><span className="brand-mark"><UiIcon name="hand" /></span><span>ViSign</span><span className="brand-divider" /><span className="brand-description">Ngôn ngữ ký hiệu Việt Nam</span></div>
          <div className="header-actions"><span className="version-label">Bản thử nghiệm</span><CameraHelp recordingEnabled={recordingEnabled} recognitionEnabled={!!recognition} /></div>
        </div>
        <div className="camera-status-row">
          <span className="workspace-label"><UiIcon name="camera" />Không gian nhận diện</span>
          <div className="camera-status-actions">
            <div className={`status-badge ${hasCamera ? 'is-live' : ''} ${state === 'permission' ? 'is-waiting' : ''}`}><span className="status-dot" aria-hidden="true" />{badge}</div>
            {hasCamera && <button className="icon-button reset-button" onClick={reset} aria-label="Đặt lại" title="Tắt camera và đặt lại"><UiIcon name="reset" /></button>}
          </div>
        </div>
        <div className="camera-intro"><h2>{instruction}</h2><p>{description}</p>
          {recognition?.model && <ModelNotice model={recognition.model} />}
          {recognition?.modelStatus === 'loading' && <p role="status">Đang đọc phạm vi nhận diện…</p>}
        </div>
        <div className="guide-space">
          <FramingGuide />
          {!hasCamera && !error && <span className="guide-caption">Khuôn mặt và hai tay trong khung hình</span>}
          {error && <div className="outcome-card error-message" role="alert"><span className="outcome-icon"><UiIcon name="camera" /></span><strong>{error.title}</strong><p>{error.guidance}</p></div>}
          {clip && !error && <div className="outcome-card clip-message" role="status"><span className="outcome-icon"><UiIcon name="check" /></span><h3>Đã quay xong</h3><p>Đoạn quay của bạn đã sẵn sàng.<br />Tính năng nhận diện đang được hoàn thiện.</p></div>}
          {!error && recognition?.modelError && <div className="outcome-card"><RecognitionError error={recognition.modelError} onRetry={recognition.retry} /></div>}
          {!error && attempt?.phase === 'error' && <div className="outcome-card"><RecognitionError error={attempt.error} onRetry={recognition!.retry} /></div>}
          {!error && attempt?.phase === 'result' && <div className="outcome-card"><RecognitionResult result={attempt.result} onRetry={recognition!.cancel} /></div>}
        </div>
        {(!hasCamera || recordingEnabled || (recognition && !outcome)) && <div className="camera-bottom">
          <div className="capture-controls" role="group" aria-label={vi.a11y.cameraControls}>
            {(state === 'idle' || state === 'error') && <button className="primary-button" onClick={() => void enableCamera()} aria-label={state === 'error' ? vi.actions.retry : vi.actions.enableCamera}><UiIcon name="camera" />{state === 'error' ? vi.actions.retry : vi.actions.enableCamera}<UiIcon name="arrow" /></button>}
            {state === 'permission' && <><span className="permission-pending"><span className="loading-spinner" />Đang chờ bạn cho phép</span><button className="text-button" onClick={cancel}>{vi.actions.cancelRequest}</button></>}
            {state === 'ready' && !recognition && <button className="primary-button" onClick={startRecording} aria-label={clip ? vi.actions.recordAgain : vi.actions.startRecording}><span className="record-symbol" />{clip ? vi.actions.recordAgain : vi.actions.startRecording}</button>}
            {state === 'ready' && recognition && !captured && !submitting && !outcome && <button className="primary-button" disabled={!canRecognize} onClick={startRecording}><UiIcon name="hand" />Nhận diện</button>}
            {state === 'recording' && <button className="primary-button stop-button" onClick={stopRecording}><span className="stop-symbol" />{recognition ? 'Kết thúc' : vi.actions.stopRecording}</button>}
            {state === 'stopping' && <span className="permission-pending"><span className="loading-spinner" />Đang hoàn tất…</span>}
            {isCapturing && <button className="text-button cancel-button" onClick={cancel}>{vi.actions.cancelRecording}</button>}
            {captured && <><button className="primary-button" onClick={() => void recognition?.submit()}>Gửi nhận diện<UiIcon name="arrow" /></button><button className="text-button" onClick={cancel}>Hủy đoạn quay</button></>}
            {submitting && <><span className="permission-pending"><span className="loading-spinner" />Đang xử lý…</span><button className="text-button" onClick={cancel}>Hủy yêu cầu</button></>}
          </div>
          <p className="control-caption"><UiIcon name="shield" />{hasCamera && recognition ? 'Nhận diện ghi một đoạn camera ngắn. Chỉ gửi khi bạn chọn Gửi nhận diện.' : hasCamera ? 'Chỉ ghi hình khi bạn nhấn quay · Không ghi âm' : 'Camera chỉ bật khi bạn cho phép'}</p>
        </div>}
      </div>
      <p className="sr-only" role="status" aria-live="polite" aria-label={vi.a11y.recognitionStatus}>{status}</p>
    </section>
  );
}
