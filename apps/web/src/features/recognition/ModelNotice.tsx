import type { ModelInfo } from '../../types/inference-api';
import { vi } from '../../content/vi';

export function ModelNotice({ model }: { model: ModelInfo }) {
  const fullReady = model.artifactKind === 'full' && model.demoReady && model.meanings.length === 10
    && model.macroF1 !== null && model.macroF1 >= 0.8 && model.perMeaningRecall !== null
    && model.meanings.every(meaning => (model.perMeaningRecall?.[meaning] ?? -1) >= 0.65);
  const label = model.artifactKind === 'fixture' ? 'Kiểm thử tích hợp · Kết quả tạo sẵn'
    : model.artifactKind === 'pilot' ? 'Model pilot · Phạm vi giới hạn'
    : fullReady ? 'Sẵn sàng demo MVP' : 'Model đầy đủ · Chưa sẵn sàng demo';
  return (
    <div className={`model-notice ${fullReady ? 'model-ready' : 'model-limited'}`}>
      <span>{label}</span>
      <details className="model-details"><summary>Phạm vi · {model.meanings.length} ý nghĩa</summary>
        <div className="model-details-content">
          <strong>{vi.model.supportedMeanings}</strong><ul>{model.meanings.map((meaning, index) => <li key={`${index}-${meaning}`}>{meaning}</li>)}</ul>
          {!fullReady && <p>{vi.model.notices[model.artifactKind]}</p>}
          <dl><dt>Phiên bản model</dt><dd>{model.modelVersion}</dd><dt>Dữ liệu</dt><dd>{model.datasetVersion}</dd><dt>Extractor</dt><dd>{model.extractorVersion}</dd><dt>Feature schema</dt><dd>{model.featureSchemaVersion}</dd><dt>Macro-F1</dt><dd>{model.macroF1 === null ? 'Chưa đánh giá' : `${(model.macroF1 * 100).toFixed(1)}%`}</dd></dl>
        </div>
      </details>
    </div>
  );
}
