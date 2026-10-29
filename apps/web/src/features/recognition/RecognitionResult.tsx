import { useEffect, useRef } from 'react';
import { vi } from '../../content/vi';
import type { PredictionResponse } from '../../types/inference-api';
import { UiIcon } from '../../components/UiIcon';

export function RecognitionResult({ result, onRetry }: { result: PredictionResponse; onRetry: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), [result]);
  return (
    <section className="recognition-result" aria-label={vi.a11y.recognitionResult}>
      <span className="outcome-icon"><UiIcon name={result.accepted ? 'check' : 'help'} /></span>
      <p className="result-kicker">{result.accepted ? vi.result.accepted : 'Chưa có kết quả chắc chắn'}</p>
      <h3 ref={heading} tabIndex={-1}>{result.accepted ? result.text : vi.result.rejected}</h3>
      <p className="confidence">{vi.result.confidence}: <strong>{new Intl.NumberFormat('vi-VN', { style: 'percent', maximumFractionDigits: 1 }).format(result.confidence)}</strong></p>
      {!result.accepted && <p>{vi.result.retryGuidance}</p>}
      <button className="text-button retry-button" onClick={onRetry}>{vi.actions.retry}<UiIcon name="reset" /></button>
      <p className="result-disclaimer">{vi.disclaimer}</p>
    </section>
  );
}
