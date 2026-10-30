# Backend/API Work Dashboard

| Field | Value |
|---|---|
| Worker ID | `P2` |
| Role ID | `backend-api` |
| Current member | Tín |
| Scope | FastAPI domain, API contract, predictor integration, cleanup, privacy and artifact rollback |
| Last updated | 2026-10-29 |

## Current Progress

| Task | Status | Next action / Blocker | Evidence |
|---|---|---|---|
| T019 | DONE | Model metadata & gate evaluation implemented | `services/inference-api/src/visign_api/domain/model_version.py` |
| T020 | DONE | Prediction states, timings and quality hints defined | `services/inference-api/src/visign_api/domain/prediction.py` |
| T021 | DONE | Stable error catalog and ErrorEnvelope implemented | `services/inference-api/src/visign_api/domain/errors.py` |
| T022 | DONE | Model path, MIME, limits, timeouts and CORS configured | `services/inference-api/src/visign_api/config.py` |
| T023 | DONE | Privacy-safe structured JSON logging implemented | `services/inference-api/src/visign_api/observability.py` |
| T024 | DONE | Temporary clip lifecycle with guaranteed deletion implemented | `services/inference-api/src/visign_api/inference/temporary_clip.py` |
| T025 | DONE | Guaranteed cleanup unit tests passed | `services/inference-api/tests/unit/test_temporary_clip.py` (3 passed) |
| T026 | DONE | FastAPI app, router, X-Request-ID, bounded inference & error mapping | `services/inference-api/src/visign_api/main.py`, `router.py` |
| T030 | DONE | Fixture artifact and prediction contract tests passed | `services/inference-api/tests/contract/test_predictions_contract.py` |
| T037 | DONE | Predictor interface, fixture adapter & rollback registry implemented | `services/inference-api/src/visign_api/inference/predictor.py` |
| T038 | DONE | POST /api/v1/predictions endpoint implemented | `services/inference-api/src/visign_api/api/predictions.py` |
| T044 | DONE | Pure confidence decision boundary unit tests passed | `services/inference-api/tests/unit/test_prediction_decision.py` (5 passed) |
| T045 | DONE | Contract tests for 4xx, 503, 500, low-confidence 200 passed | `services/inference-api/tests/contract/test_predictions_contract.py` |
| T048 | DONE | Pure confidence decision logic implemented | `services/inference-api/src/visign_api/inference/prediction_decision.py` |
| T049 | DONE | Clip MIME, size, WebM magic bytes validation implemented | `services/inference-api/src/visign_api/inference/clip_validator.py` |
| T050 | DONE | Endpoint cleanup and error mapping completed | `services/inference-api/src/visign_api/api/predictions.py` |
| T055 | DONE | Health and model-info contract tests passed | `services/inference-api/tests/contract/test_model_info_contract.py` (3 passed) |
| T060 | DONE | GET /health and GET /model-info endpoints implemented | `services/inference-api/src/visign_api/api/system.py` |
| T064 | DONE | E2E prediction pipeline and artifact swap tests passed | `tests/integration/test_prediction_pipeline.py` (2 passed) |
| T066 | DONE | Privacy audit asserting zero video/PII leakage passed | `tests/integration/test_prediction_privacy.py` (1 passed) |

## Checkpoint Responsibilities

- Keep the prediction endpoint stable across fixture, pilot and full.
- Validate `featureSchemaVersion` before loading pilot/full artifacts.
- Maintain the last smoke-tested artifact path for rollback.
- Confirm temporary input deletion for success and every failure path.

## Handoff Notes

- Current risks: Predictor depends on artifact metadata agreed with Cường.
- Required reviewers: `training-models` for T019/T037/T049/T055/T060; Huy for T064/T066 evidence.
- Work-in-progress limit: Maximum 2 tasks in `DOING`.

### Review & test pass 2026-10-30

Fixed:

- Pilot/full artifacts were silently served by `FixturePredictor` (fake "Xin chào" 0.95, even for a
  `demoReady=true` full model). They now fail closed via `PREDICTOR_FACTORIES` until the GRU predictor
  is registered; the last working artifact is kept.
- Loader now rejects a `featureSchemaVersion` mismatch (`FEATURE_SCHEMA_VERSION`, default
  `vsl-feature-v1.0`), duplicate/unmapped `classLabels`, a `meaningMap` that does not match
  `meanings`, missing `displayTextMap` text, pilot > 3 meanings and full ≠ 10 meanings.
- `predictor.predict()` blocked the event loop, so `SERVICE_BUSY` could never trigger and `/health`
  froze during inference. It now runs in a threadpool while holding the inference slot.
- Unexpected predictor errors map to 500 `PREDICTION_FAILED` and are logged with a trace.
  `processingTimeMs` is measured from request start, and success logs include `timingsMs`.
- A rejected `PredictionResponse` with a non-null `classLabel` is now invalid.
- JSON logs were dropped on Windows when stdout was redirected (cp1252 + Vietnamese text); logs are
  now ASCII-escaped JSON. Log records also carry the exception trace.
- CORS was `*` with credentials. It now defaults to the Vite dev/preview origins without credentials;
  override with `CORS_ORIGINS='["http://host:port"]'`.
- The default `MODEL_ARTIFACT_PATH` no longer depends on the cwd.
- Added `tests/fixtures/model-artifacts/fixture-low-confidence/` (`fixtureResponse`) for
  low-confidence contract/E2E tests (T045, T047).

Tests: 84/84 pass (`python -m pytest` from repo root). New tests cover low-confidence 200,
`MODEL_NOT_READY` 503, `PREDICTION_FAILED` 500, real concurrent `SERVICE_BUSY`, degraded startup,
rollback, artifact consistency, response invariants, clip validators and the log formatter. Mutation
checks confirmed the new tests fail when the old bugs are reintroduced. A live uvicorn smoke test
passed for health, model-info, predict, 415, 422 and CORS.

Still open (blocked on Person P3/Cường):

- T037 pilot/full: register a GRU predictor factory once `visign_ai.landmarks` (T015/T016) and the
  artifact format from T036 exist.
- T049: decoder probe, PTS duration, no-person and landmark sufficiency need the real `VideoDecoder`
  and extractor. `validate_clip_duration()` is ready for the predictor to call after decoding.
  Thresholds for `NO_PERSON_DETECTED`/`INSUFFICIENT_LANDMARKS` are not specified yet.

## Handoff History

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-10-22 | — | Tín | Initial assignment; 20 open tasks |
| 2026-10-29 | Tín | Ready for FE/AI | Completed all 20 backend tasks (T019-T026, T030, T037-T038, T044-T045, T048-T050, T055, T060, T064, T066); 21/21 pytest passed |
| 2026-10-30 | Tín (review) | Tín | Review/test pass: 8 defects fixed, 84/84 pytest; T037 pilot/full and T049 decode/landmark checks blocked on T015/T016/T036 (see Review & test pass) |
