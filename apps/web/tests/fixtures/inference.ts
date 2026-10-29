import type { ModelInfo, PredictionResponse } from '../../src/types/inference-api';

export const requestId = '12345678-1234-4234-8234-123456789abc';
export const model: ModelInfo = {
  modelVersion: 'fixture-1', artifactKind: 'fixture', datasetVersion: 'test-only',
  extractorVersion: 'test-extractor', featureSchemaVersion: 'test-schema',
  meanings: ['Xin chào'], acceptanceThreshold: 0.8, macroF1: null,
  perMeaningRecall: null, evaluatedAt: null, demoReady: false,
};
export const accepted: PredictionResponse = {
  requestId, text: 'Xin chào', classLabel: 'hello', confidence: 0.94,
  accepted: true, modelVersion: model.modelVersion, processingTimeMs: 40,
};
