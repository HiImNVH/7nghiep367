import { useCallback, useEffect, useReducer, useRef } from 'react';
import { inferenceApi, InferenceApiError, type InferenceApi } from '../../services/inferenceApi';
import type { ModelInfo, PredictionResponse } from '../../types/inference-api';

type Attempt =
  | { phase: 'idle' | 'capturing' }
  | { phase: 'captured'; clip: Blob }
  | { phase: 'submitting' }
  | { phase: 'result'; result: PredictionResponse }
  | { phase: 'error'; error: InferenceApiError };
interface State {
  model: ModelInfo | null;
  modelStatus: 'loading' | 'ready' | 'error';
  modelError: InferenceApiError | null;
  attempt: Attempt;
}
type Event =
  | { type: 'MODEL_LOADING' }
  | { type: 'MODEL_READY'; model: ModelInfo }
  | { type: 'MODEL_ERROR'; error: InferenceApiError }
  | { type: 'ATTEMPT'; attempt: Attempt };
const initial: State = { model: null, modelStatus: 'loading', modelError: null, attempt: { phase: 'idle' } };
function reducer(state: State, event: Event): State {
  switch (event.type) {
    case 'MODEL_LOADING': return { ...initial };
    case 'MODEL_READY': return { ...state, model: event.model, modelStatus: 'ready', modelError: null };
    case 'MODEL_ERROR': return { ...initial, modelStatus: 'error', modelError: event.error };
    case 'ATTEMPT': return { ...state, attempt: event.attempt };
  }
}

export function useRecognition(api: InferenceApi = inferenceApi) {
  const [state, dispatch] = useReducer(reducer, initial);
  const modelRef = useRef<ModelInfo | null>(null);
  const clipRef = useRef<Blob | null>(null);
  const modelAbort = useRef<AbortController | null>(null);
  const predictAbort = useRef<AbortController | null>(null);
  const modelGeneration = useRef(0);
  const attemptGeneration = useRef(0);

  const cancel = useCallback(() => {
    attemptGeneration.current += 1;
    predictAbort.current?.abort();
    predictAbort.current = null;
    clipRef.current = null;
    dispatch({ type: 'ATTEMPT', attempt: { phase: 'idle' } });
  }, []);
  const reloadModel = useCallback(async () => {
    cancel();
    modelAbort.current?.abort();
    const generation = ++modelGeneration.current;
    const controller = new AbortController();
    modelAbort.current = controller;
    modelRef.current = null;
    dispatch({ type: 'MODEL_LOADING' });
    try {
      const model = await api.modelInfo({ signal: controller.signal });
      if (generation !== modelGeneration.current || controller.signal.aborted) return;
      modelRef.current = model;
      dispatch({ type: 'MODEL_READY', model });
    } catch (cause) {
      if (generation !== modelGeneration.current || controller.signal.aborted) return;
      dispatch({ type: 'MODEL_ERROR', error: cause instanceof InferenceApiError ? cause : new InferenceApiError('network') });
    }
  }, [api, cancel]);
  useEffect(() => {
    void reloadModel();
    return () => {
      modelGeneration.current += 1;
      attemptGeneration.current += 1;
      modelAbort.current?.abort();
      predictAbort.current?.abort();
      modelRef.current = null;
      clipRef.current = null;
    };
  }, [reloadModel]);

  const beginCapture = useCallback(() => {
    if (!modelRef.current || predictAbort.current) return false;
    cancel();
    dispatch({ type: 'ATTEMPT', attempt: { phase: 'capturing' } });
    return true;
  }, [cancel]);
  const captureReady = useCallback((clip: Blob) => {
    clipRef.current = clip;
    dispatch({ type: 'ATTEMPT', attempt: { phase: 'captured', clip } });
  }, []);
  const submit = useCallback(async () => {
    const clip = clipRef.current;
    const model = modelRef.current;
    if (!clip || !model || predictAbort.current) return;
    clipRef.current = null;
    const generation = ++attemptGeneration.current;
    const controller = new AbortController();
    predictAbort.current = controller;
    dispatch({ type: 'ATTEMPT', attempt: { phase: 'submitting' } });
    try {
      const result = await api.predict(clip, { signal: controller.signal });
      if (generation !== attemptGeneration.current || controller.signal.aborted) return;
      if (result.modelVersion !== model.modelVersion) {
        modelRef.current = null;
        dispatch({ type: 'MODEL_ERROR', error: new InferenceApiError('MODEL_NOT_READY', result.requestId) });
        dispatch({ type: 'ATTEMPT', attempt: { phase: 'idle' } });
        return;
      }
      dispatch({ type: 'ATTEMPT', attempt: { phase: 'result', result } });
    } catch (cause) {
      if (generation !== attemptGeneration.current || controller.signal.aborted) return;
      dispatch({ type: 'ATTEMPT', attempt: { phase: 'error', error: cause instanceof InferenceApiError ? cause : new InferenceApiError('network') } });
    } finally {
      if (generation === attemptGeneration.current) predictAbort.current = null;
    }
  }, [api]);
  const retry = useCallback(() => {
    cancel();
    // Refresh scope after an error/artifact swap, never replay an upload automatically.
    void reloadModel();
  }, [cancel, reloadModel]);
  return { ...state, cancel, reloadModel, beginCapture, captureReady, submit, retry };
}
export type RecognitionController = ReturnType<typeof useRecognition>;
