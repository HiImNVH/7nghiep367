import { useEffect, useState } from 'react';

type Phase = 'idle' | 'preparing' | 'ready' | 'training' | 'evaluating' | 'complete' | 'failed';
type PilotStatus = {
  phase: Phase;
  id?: string;
  updatedAt?: number;
  title?: string;
  group?: 'sot-cho';
  sampleTotal?: number;
  testCount?: number;
  wandbDirectory?: string;
  wandbProject?: string;
  epoch?: number;
  epochs?: number;
  accepted?: number;
  rejected?: { sampleId: string; code: string }[];
  wandbUrl?: string;
  wandbMode?: string;
  wandbRunId?: string;
  metrics?: { accuracy: number; macroF1?: number };
  error?: string;
};

const phaseText: Record<Phase, string> = {
  idle: 'Chưa kiểm tra dữ liệu',
  preparing: 'Đang trích landmark v0.3',
  ready: 'Đủ 6 clip để train thử',
  training: 'Đang train GRU',
  evaluating: 'Đang đánh giá tập test',
  complete: 'Hoàn tất pilot',
  failed: 'Job dừng',
};

class PilotAuthError extends Error {}

async function request<T = PilotStatus>(code: string, action?: 'prepare' | 'train' | 'history', signal?: AbortSignal): Promise<T> {
  const response = await fetch('/api/admin/pilot' + (action ? '/' + action : ''), {
    method: action === 'prepare' || action === 'train' ? 'POST' : 'GET',
    headers: { Authorization: 'Bearer ' + code },
    ...(signal ? { signal } : {}),
  });
  if (response.status === 404) throw new Error('API pilot chưa sẵn sàng. Khởi động lại backend từ terminal VS Code theo README Admin.');
  if (response.status === 401) throw new PilotAuthError('Mã admin không đúng. Vui lòng nhập lại.');
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Không đọc được trạng thái pilot.');
  return body;
}

function RunTracking({ status }: { status: PilotStatus }) {
  if (!status.wandbUrl && status.wandbMode !== 'offline') return null;
  return <section className="pilot-wandb" aria-label="Theo dõi trên W&B">
    <h3>Weights &amp; Biases</h3>
    {status.wandbUrl && <a className="workspace-link" href={status.wandbUrl} target="_blank" rel="noreferrer">Mở biểu đồ W&amp;B ↗</a>}
    {status.wandbMode === 'offline' && !status.wandbUrl && <>
      <p><strong>Log offline</strong> · Run <code>{status.wandbRunId}</code></p>
      {status.id && status.wandbRunId && status.phase === 'complete' && <details>
        <summary>Cách mở run trên web W&amp;B</summary>
        <p>Chạy trong PowerShell của VS Code tại gốc repo. Sau khi sync, mở URL được in ra.</p>
        <pre>{[
          '.\\.venv-ai\\Scripts\\wandb.exe login',
          '$run = Get-ChildItem "' + (status.wandbDirectory ?? '.local/pilot-runs/' + status.id + '/wandb') + '" -Directory -Filter "offline-run-*-' + status.wandbRunId + '"',
          '.\\.venv-ai\\Scripts\\wandb.exe sync --project ' + (status.wandbProject ?? 'visign-pilot') + ' $run.FullName',
        ].join('\n')}</pre>
      </details>}
    </>}
  </section>;
}

function HistoryCard({ job }: { job: PilotStatus }) {
  return <li>
      <div className="pilot-status">
        <strong>{job.title ?? 'Lần chạy Admin'}</strong><span>{phaseText[job.phase]}</span>
        <span>Job <code>{job.id}</code></span>
        {job.updatedAt !== undefined && <time dateTime={new Date(job.updatedAt * 1000).toISOString()}>
          {new Date(job.updatedAt * 1000).toLocaleString('vi-VN')}
        </time>}
      </div>
      <div className="pilot-history-summary">
        {job.accepted !== undefined && <span>{job.accepted}/{job.sampleTotal ?? 6} clip đạt</span>}
        {job.epoch !== undefined && job.epochs !== undefined && <span>Epoch {job.epoch}/{job.epochs}</span>}
        {job.metrics && <span>Accuracy {(job.metrics.accuracy * 100).toFixed(1)}%{job.metrics.macroF1 !== undefined && ' · Macro-F1 ' + job.metrics.macroF1.toFixed(3)}{job.testCount !== undefined && ' · ' + job.testCount + ' clip test'}</span>}
      </div>
      {job.epoch !== undefined && job.epochs !== undefined &&
        <progress className="pilot-progress" aria-label={'Tiến độ job ' + job.id} value={job.epoch} max={job.epochs} />}
      {job.error && <p className="pilot-error">{job.error}</p>}
      <RunTracking status={job} />
  </li>;
}

function HistoryList({ jobs }: { jobs: PilotStatus[] | undefined }) {
  if (!jobs) return null;
  if (!jobs.length) return <p>Chưa có job pilot nào.</p>;
  const pilot = jobs.filter(job => job.group === 'sot-cho');
  return <div className="pilot-history">
    {jobs.map(job => job.group === 'sot-cho'
      ? job === pilot[0] && <details key="sot-cho" className="pilot-history-group">
        <summary><strong>Pilot Sốt + Chờ</strong> · {pilot.length} lần chạy</summary>
        <ul className="pilot-history">{pilot.map(run => <HistoryCard key={run.id} job={run} />)}</ul>
      </details>
      : <ul key={job.id} className="pilot-history"><HistoryCard job={job} /></ul>)}
  </div>;
}

export default function PilotPanel({ token, onToken, showHistory }: { token: string; onToken: (token: string) => void; showHistory: boolean }) {
  const [draft, setDraft] = useState('');
  const [status, setStatus] = useState<PilotStatus>();
  const [jobs, setJobs] = useState<PilotStatus[]>();
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const phase = status?.phase;
  const active = phase === 'preparing' || phase === 'training' || phase === 'evaluating';

  useEffect(() => {
    if (!token) return;
    const controller = new AbortController();
    async function refresh() {
      try {
        if (showHistory) {
          const next = await request<PilotStatus[]>(token, 'history', controller.signal);
          if (!controller.signal.aborted) setJobs(next);
        } else {
          const next = await request(token, undefined, controller.signal);
          if (!controller.signal.aborted) setStatus(next);
        }
        if (!controller.signal.aborted) setError('');
      } catch (reason) {
        if (controller.signal.aborted) return;
        if (reason instanceof PilotAuthError) onToken('');
        setError(reason instanceof Error ? reason.message : String(reason));
      }
    }
    void refresh();
    const timer = active || showHistory ? window.setInterval(() => void refresh(), 1500) : undefined;
    return () => {
      controller.abort();
      window.clearInterval(timer);
    };
  }, [token, active, onToken, showHistory]);

  async function start(action: 'prepare' | 'train') {
    setPending(true);
    setError('');
    try {
      setStatus(await request(token, action));
    } catch (reason) {
      if (reason instanceof PilotAuthError) onToken('');
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setPending(false);
    }
  }

  const currentStep = status?.metrics || phase === 'evaluating' || phase === 'complete' ? 3
    : status?.accepted === 6 ? 2 : 1;

  return <div className="train-pilot">
    <p className="pilot-subtitle">{showHistory ? 'Các job đã lưu trên máy này' : <> <strong>Sốt + Chờ</strong> · Bộ dữ liệu Quang · 6 clip · Schema v0.3</>}</p>
    {!token ? <form onSubmit={event => {
      event.preventDefault();
      if (!draft.trim()) { setError('Vui lòng nhập mã admin.'); return; }
      setError('');
      onToken(draft);
      setDraft('');
    }}>
      <label>Mã admin <input type="password" value={draft} onChange={event => setDraft(event.target.value)} /></label>
      <button className="primary-button" type="submit">Tiếp tục</button>
    </form> : showHistory ? <HistoryList jobs={jobs} /> : <>
      <ol className="pilot-steps" aria-label="Các bước chạy pilot">
        {['Kiểm tra dữ liệu', 'Train GRU', 'Kết quả test'].map((label, index) =>
          <li key={label} aria-current={currentStep === index + 1 ? 'step' : undefined}
            className={currentStep > index + 1 || phase === 'complete' ? 'pilot-step-done' : ''}>
            <span>{index + 1}</span>{label}
          </li>)}
      </ol>
      <div className="pilot-status" role="status">
        <strong>{phase ? phaseText[phase] : error ? 'Không tải được trạng thái' : 'Đang tải trạng thái…'}</strong>
        {status?.accepted !== undefined && <span>{status.accepted}/6 clip đạt</span>}
        {status?.epoch !== undefined && status.epochs !== undefined &&
          <span>Epoch {status.epoch}/{status.epochs}</span>}
      </div>
      {status?.epoch !== undefined && status.epochs !== undefined &&
        <progress className="pilot-progress" aria-label="Tiến độ epoch" value={status.epoch} max={status.epochs} />}
      <div className="train-toolbar pilot-actions">
        <button type="button" disabled={pending || active || !status} onClick={() => void start('prepare')}>
          {phase === 'complete' ? 'Kiểm tra cho lần chạy mới' : 'Kiểm tra dữ liệu'}
        </button>
        {phase !== 'complete' && <button type="button" className="primary-button" disabled={pending || phase !== 'ready'}
          onClick={() => void start('train')}>Bắt đầu train thử</button>}
      </div>
    </>}
    {error && <p className="pilot-error" role="alert">{error}</p>}
    {status?.error && <p className="pilot-error" role="alert">{status.error}</p>}
    {!!status?.rejected?.length && <ul>{status.rejected.map(item => <li key={item.sampleId}>{item.sampleId} · {item.code}</li>)}</ul>}
    {status?.metrics && <section className="pilot-result" aria-label="Kết quả đánh giá">
      <h3>Kết quả trên tập test</h3>
      <dl className="pilot-metrics">
        <div><dt>Accuracy</dt><dd>{new Intl.NumberFormat('vi', {style: 'percent', maximumFractionDigits: 1}).format(status.metrics.accuracy)}</dd></div>
        <div><dt>Macro-F1</dt><dd>{status.metrics.macroF1?.toFixed(3) ?? '—'}</dd></div>
        <div><dt>Số clip test</dt><dd>2</dd></div>
      </dl>
      <p>Tập test có một clip mỗi nghĩa. Điểm này dùng để kiểm tra quy trình pilot.</p>
    </section>}
    {status && <RunTracking status={status} />}
    {status?.id && <p className="pilot-job">Mã job <code>{status.id}</code></p>}
  </div>;
}
