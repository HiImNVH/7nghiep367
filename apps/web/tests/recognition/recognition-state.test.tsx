import { act, renderHook, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useRecognition } from '../../src/features/recognition/useRecognition';
import { model } from '../fixtures/inference';
import type { ModelInfo } from '../../src/types/inference-api';
import type { InferenceApi } from '../../src/services/inferenceApi';

it('a late model-info response cannot overwrite a newer scope after reload', async () => {
  let resolveOld!: (model: ModelInfo) => void;
  const api: InferenceApi = {
    health: vi.fn(), predict: vi.fn(),
    modelInfo: vi.fn().mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }))
      .mockResolvedValue({ ...model, artifactKind: 'pilot', modelVersion: 'pilot-new' }),
  };
  const { result } = renderHook(() => useRecognition(api));
  await act(async () => { await result.current.reloadModel(); });
  await waitFor(() => expect(result.current.model?.modelVersion).toBe('pilot-new'));
  await act(async () => resolveOld(model));
  expect(result.current.model?.modelVersion).toBe('pilot-new');
});
