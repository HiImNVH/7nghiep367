import { useEffect, useRef } from 'react';
import { apiErrors, requestErrors } from '../../content/vi';
import { InferenceApiError } from '../../services/inferenceApi';

export function RecognitionError({ error, onRetry }: { error: InferenceApiError; onRetry: () => void }) {
  const title = useRef<HTMLHeadingElement>(null);
  useEffect(() => title.current?.focus(), [error]);
  const copy = error.code in apiErrors ? apiErrors[error.code as keyof typeof apiErrors]
    : error.code in requestErrors ? requestErrors[error.code as keyof typeof requestErrors] : requestErrors.unknown;
  return (
    <section className="recognition-error" role="alert">
      <h3 ref={title} tabIndex={-1}>{copy.title}</h3><p>{copy.guidance}</p>
      {error.retryAfter !== undefined && <p>Hãy chờ khoảng {error.retryAfter} giây trước khi thử lại.</p>}
      <button className="text-button retry-button" onClick={onRetry}>Thử lại</button>
      {error.requestId && <details className="error-reference"><summary>Mã yêu cầu hỗ trợ</summary><code>{error.requestId}</code></details>}
    </section>
  );
}
