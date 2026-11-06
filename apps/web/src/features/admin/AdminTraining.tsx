import PilotPanel from './PilotPanel';
import { UiIcon } from '../../components/UiIcon';
import { useEffect, useRef, useState } from 'react';
import { frameName, readDemoCsv, readResultZip } from './demoResults';
import './admin.css';

type Row = Record<string, string>;
type Result = {
  files: Map<string, Blob>;
  frames: Row[];
  points: Map<number, Row[]>;
  report: string;
  schema: string;
  archive?: Blob;
};

function useBlobUrl(blob: Blob | undefined) {
  const [url, setUrl] = useState<string>();
  useEffect(() => {
    if (!blob) { setUrl(undefined); return; }
    const value = URL.createObjectURL(blob);
    setUrl(value);
    return () => URL.revokeObjectURL(value);
  }, [blob]);
  return url;
}

async function loadResult(files: Map<string, Blob>, archive?: Blob): Promise<Result> {
  async function read(name: string) {
    const file = files.get(name);
    if (!file) throw new Error('Thiếu ' + name + ' trong thư mục kết quả Demo 2.');
    return file.text();
  }
  const [report, schema, summary, coordinates] = await Promise.all([
    read('report.json'), read('feature_schema.json'), read('frames-summary.csv'), read('landmarks.csv'),
  ]);
  JSON.parse(report);
  const version = JSON.parse(schema).featureSchemaVersion;
  const frames = readDemoCsv(summary);
  if (version !== 'demo2-xy-32-v0.2-draft' || !frames.length ||
      frames.some((row, i) => Number(row.frame) !== i || !files.has(frameName(i)))) {
    throw new Error('Chọn đúng thư mục kết quả Demo 2 v0.2 có đầy đủ ảnh frame.');
  }
  const points = new Map<number, Row[]>();
  for (const row of readDemoCsv(coordinates)) {
    const index = Number(row.frame);
    const list = points.get(index) ?? [];
    list.push(row);
    points.set(index, list);
  }
  if (frames.some((_, index) => points.get(index)?.length !== 78)) {
    throw new Error('Bảng tọa độ không đủ 78 điểm cho từng frame.');
  }
  return { files, frames, points, report, schema, ...(archive ? { archive } : {}) };
}

class AdminCodeError extends Error {}

async function inspectRequest(token: string, body: FormData) {
  const response = await fetch('/api/admin/inspect', {
    headers: { Authorization: 'Bearer ' + token },
    method: 'POST', body,
  });
  if (response.status === 401) throw new AdminCodeError();
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(typeof error?.detail === 'string' ? error.detail : 'Backend báo lỗi ' + response.status);
  }
  return response;
}

function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const statusLabels: Record<string, string> = {
  VALID: 'Hợp lệ',
  LOW_CONFIDENCE_OR_OUTSIDE: 'Ước lượng yếu / ngoài khung',
  NOT_DETECTED: 'Không thấy',
};

export default function AdminTraining() {
  const videoInput = useRef<HTMLInputElement>(null);
  const folderInput = useRef<HTMLInputElement>(null);
  const details = useRef<HTMLDialogElement>(null);
  const [detailView, setDetailView] = useState<'overview' | 'report' | 'schema' | 'files'>('files');
  const [token, setToken] = useState('');
  const [clip, setClip] = useState<File>();
  const [result, setResult] = useState<Result>();
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const pilotDialog = useRef<HTMLDialogElement>(null);
  const [pilotOpen, setPilotOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const authDialog = useRef<HTMLDialogElement>(null);
  const codeInput = useRef<HTMLInputElement>(null);
  const [authMessage, setAuthMessage] = useState('');
  const preview = useBlobUrl(result?.files.get(frameName(index)));
  const overview = useBlobUrl(result?.files.get('landmark-preview.png'));
  const frame = result?.frames[index];
  const next = result?.frames[index + 1];
  const points = result?.points.get(index) ?? [];
  const ordered = [...points.slice(42, 48), ...points.slice(0, 42), ...points.slice(48)];
  const report = result ? JSON.parse(result.report) : null;

  useEffect(() => {
    if (!playing || !frame || !next) return;
    const delay = Math.max(20, Number(next.timestamp_ms) - Number(frame.timestamp_ms));
    const timer = window.setTimeout(() => {
      setIndex(index + 1);
      if (index + 2 === result?.frames.length) setPlaying(false);
    }, delay);
    return () => window.clearTimeout(timer);
  }, [playing, index, frame, next, result]);

  async function open(read: () => Promise<Result>) {
    setBusy(true);
    setPlaying(false);
    setMessage('Đang đọc kết quả…');
    try {
      const value = await read();
      const both = JSON.parse(value.report).bothHandsAndShouldersFrames as number[] | undefined;
      const preferred = both?.[Math.floor(both.length / 2)] ?? 0;
      setIndex(value.frames[preferred] ? preferred : 0);
      setResult(value);
      setMessage('Đã mở ' + value.frames.length + ' frame.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  function promptForCode(message: string) {
    setAuthMessage(message);
    if (codeInput.current) codeInput.current.value = '';
    authDialog.current?.showModal();
    codeInput.current?.focus();
  }

  function inspect(code: string) {
    if (!clip || busy) return;
    if (!code.trim()) {
      promptForCode('Nhập mã admin để chạy kiểm tra.');
      return;
    }

    void open(async () => {
      const body = new FormData();
      body.append('video', clip);
      try {
        const archive = await (await inspectRequest(code, body)).blob();
        setToken(code);
        return loadResult(await readResultZip(archive), archive);
      } catch (error) {
        if (error instanceof AdminCodeError) {
          setToken('');
          promptForCode('Mã admin không đúng. Vui lòng nhập lại.');
          throw new Error('Cần mã admin để chạy kiểm tra.', { cause: error });
        }
        throw error;
      }
    });
  }


  function importFolder(files: FileList | null) {
    if (!files?.length) return;
    const entries = new Map<string, Blob>();
    for (const file of files) {
      const path = file.webkitRelativePath.split('/').slice(1).join('/');
      entries.set(path, file);
    }
    void open(() => loadResult(entries));
  }

  function go(value: number) {
    setPlaying(false);
    setIndex(value);
  }

  function showDetails(view: 'overview' | 'report' | 'schema' | 'files') {
    setDetailView(view);
    details.current?.showModal();
  }

  function downloadFile(name: string) {
    const file = result?.files.get(name);
    if (file) download(file, name.split('/').at(-1) ?? name);
  }

  return (
    <main className="app-shell">
      <div className="train-admin">
        <header className="panel-topbar">
          <div className="brand">
            <span className="brand-mark"><UiIcon name="hand" /></span><span>ViSign</span>
            <span className="brand-divider" /><span className="brand-description">Demo 2 · Kiểm tra landmark</span>
          </div>
          <a className="workspace-link" href="/">← Trang nhận diện</a>
        </header>
        <section className="train-controls" aria-label="Công cụ kiểm tra">
          <div className="train-heading">
            <h1>Kiểm tra dữ liệu train <span>Demo 2 v0.2</span></h1>
          </div>
          <div className="train-toolbar" role="group" aria-label="Thao tác chính">
            <input hidden ref={videoInput} type="file" accept=".mp4,.webm" aria-label="Video" onChange={e => setClip(e.target.files?.[0])} />
            <input hidden ref={folderInput} type="file" {...{ webkitdirectory: '' }} multiple aria-label="Thư mục kết quả"
              onChange={e => { importFolder(e.target.files); e.target.value = ''; }} />
            <button type="button" disabled={busy} onClick={() => videoInput.current?.click()}>Chọn video</button>
            <button className="primary-button" type="button" disabled={busy || !clip} onClick={() => inspect(token)}>{busy ? 'Đang xử lý…' : 'Chạy kiểm tra'}</button>
            <button type="button" disabled={busy} onClick={() => folderInput.current?.click()}>Mở kết quả cũ</button>
            <button type="button" disabled={!result?.files.has('landmarks.csv')} onClick={() => downloadFile('landmarks.csv')}>Tọa độ CSV</button>
            <button type="button" disabled={!result?.files.has('frames-summary.csv')} onClick={() => downloadFile('frames-summary.csv')}>Từng frame CSV</button>
            <button type="button" disabled={!result} onClick={() => showDetails('files')}>Tệp kết quả</button>
            <button type="button" disabled={!result?.archive} onClick={() => {
              if (result?.archive) download(result.archive, 'visign-demo2-result.zip');
            }}>Tải ZIP</button>
          </div>
          <div className="train-info">
            <button type="button" onClick={() => {
              setShowHistory(false);
              setPilotOpen(true);
              pilotDialog.current?.showModal();
            }}>Huấn luyện pilot</button>
            <button type="button" onClick={() => {
              setShowHistory(true);
              setPilotOpen(true);
              pilotDialog.current?.showModal();
            }}>Lịch sử train</button>
            <p role="status">{[clip?.name, message].filter(Boolean).join(' · ') || 'Chọn MP4, WebM hoặc mở kết quả Demo 2 đã lưu.'}</p>
          </div>
        </section>
        {result && frame ? <section className="train-result" aria-label="Kết quả clip">
          <div className="train-result-bar">
            <p><strong>{result.frames.length} frame</strong> · Hai tay cùng thấy {report.bothHandsFrames?.length ?? 0} frame · Tensor {report.tensorShape?.join(' × ')} · {report.inputStatus}</p>
            <div className="train-detail-actions">
              <button type="button" disabled={!overview} onClick={() => showDetails('overview')}>Tổng quan</button>
              <button type="button" onClick={() => showDetails('report')}>Báo cáo</button>
              <button type="button" onClick={() => showDetails('schema')}>Schema clip</button>
            </div>
          </div>
          <div className="train-nav">
            <button type="button" disabled={index === 0} onClick={() => go(index - 1)}>Trước</button>
            <button type="button" disabled={result.frames.length < 2} onClick={() => {
              if (!playing && !next) setIndex(0);
              setPlaying(!playing);
            }}>{playing ? 'Dừng' : 'Phát'}</button>
            <input aria-label="Chọn frame" type="range" min="0" max={result.frames.length - 1} value={index} onChange={e => go(Number(e.target.value))} />
            <button type="button" disabled={!next} onClick={() => go(index + 1)}>Sau</button>
            <span>Frame {index} / {result.frames.length - 1} · {Math.round(Number(frame.timestamp_ms))} ms</span>
          </div>
          <div className="train-frame">
            <figure className="train-preview">
              <div className="train-image">{preview && <img src={preview} alt={'Landmark frame ' + index} />}</div>
              <figcaption>
                <strong>Tay L {frame.left_hand_points}/21 · Tay R {frame.right_hand_points}/21 · Vai L {frame.left_shoulder === '1' ? 'có' : 'thiếu'} · Vai R {frame.right_shoulder === '1' ? 'có' : 'thiếu'}</strong>
                <span>Xanh lá: tay L · Xanh dương: tay R · Vàng: vai/cánh tay · Tím: mặt · Xám: pose yếu · Cam: tay chưa rõ bên.</span>
                {report.duplicateHandSideFrames?.includes(index) && <span>Có hai ứng viên tay trùng nhãn bên.</span>}
              </figcaption>
            </figure>
            <div className="train-table" role="region" aria-label="Bảng tọa độ landmark" tabIndex={0}>
              <table><thead><tr>{['Điểm', 'X', 'Y', 'X px', 'Y px', 'Trạng thái', 'Visibility', 'Presence'].map(label => <th key={label}>{label}</th>)}</tr></thead>
                <tbody>{ordered.map(row => <tr key={row.landmark}><th scope="row">{row.landmark}</th>
                  {[row.x_norm, row.y_norm, row.x_px, row.y_px, statusLabels[row.status ?? ''], row.pose_visibility, row.pose_presence].map((value, i) => <td key={i}>{value || '—'}</td>)}
                </tr>)}</tbody>
              </table>
            </div>
          </div>
        </section> : <section className="train-empty">
          <span className="outcome-icon"><UiIcon name="camera" /></span>
          <h2>Chưa có clip để xem</h2>
          <p>Chạy kiểm tra một video hoặc mở kết quả cũ để xem ảnh và tọa độ theo frame.</p>
        </section>}
        <dialog ref={pilotDialog} onClose={() => setPilotOpen(false)} className="help-dialog train-dialog" aria-labelledby="train-pilot-title">
          <div className="dialog-heading">
            <h2 id="train-pilot-title">{showHistory ? 'Lịch sử train' : 'Huấn luyện pilot'}</h2>
            <form method="dialog"><button className="icon-button" aria-label="Đóng"><UiIcon name="close" /></button></form>
          </div>
          {pilotOpen && <PilotPanel token={token} onToken={setToken} showHistory={showHistory} />}
        </dialog>
        <dialog ref={authDialog} className="help-dialog train-auth" aria-labelledby="train-auth-title">
          <form onSubmit={event => {
            event.preventDefault();
            const code = codeInput.current?.value ?? '';
            if (!code.trim()) {
              setAuthMessage('Vui lòng nhập mã admin.');
              codeInput.current?.focus();
              return;
            }
            authDialog.current?.close();
            inspect(code);
          }}>
            <h2 id="train-auth-title">Nhập mã admin</h2>
            <p id="train-auth-message" role="status">{authMessage}</p>
            <label>Mã admin <input ref={codeInput} type="password" aria-describedby="train-auth-message" /></label>
            <div className="train-auth-actions">
              <button type="button" onClick={() => authDialog.current?.close()}>Hủy</button>
              <button className="primary-button" type="submit">Tiếp tục</button>
            </div>
          </form>
        </dialog>
        <dialog ref={details} className="help-dialog train-dialog" aria-labelledby="train-dialog-title">
          <div className="dialog-heading">
            <h2 id="train-dialog-title">{{ overview: 'Ảnh tổng quan', report: 'Báo cáo clip', schema: 'Schema clip', files: 'Tệp kết quả' }[detailView]}</h2>
            <form method="dialog"><button className="icon-button" aria-label="Đóng"><UiIcon name="close" /></button></form>
          </div>
          {detailView === 'overview' && overview && <img src={overview} alt="Tổng quan các frame" />}
          {detailView === 'report' && <pre>{result?.report}</pre>}
          {detailView === 'schema' && <pre>{result?.schema}</pre>}
          {detailView === 'files' && result && <div className="train-toolbar">
            {[...result.files.keys()].filter(name => !name.startsWith('frames/') || name === frameName(index)).map(name =>
              <button key={name} type="button" onClick={() => downloadFile(name)}>{name}</button>)}
          </div>}
        </dialog>
      </div>
    </main>
  );
}
