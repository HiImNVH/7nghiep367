# Tasks: ViSign VSL Recognition MVP

**Input**: Design documents from `specs/001-vsl-recognition-mvp/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/openapi.yaml](contracts/openapi.yaml)

**Tests**: Bắt buộc theo hiến pháp. Trong mỗi story, viết test và xác nhận test thất bại trước khi
thực hiện phần code tương ứng.

**Organization**: Task được nhóm theo user story để từng phần có thể kiểm thử độc lập.

**Integration tracking**: [docs/team/implementation-status.md](../../docs/team/implementation-status.md)
phân biệt evidence đang ở role branch với phần đã được review và merge vào `main`.

**Baseline reset 2026-11-03**: T001–T012 từng được đánh dấu hoàn thành trong workspace lịch sử nhưng
được mở lại khi đưa Spec Kit lên `main`, vì implementation/evidence chưa hiện diện trên `main`. Lịch sử
và branch evidence được giữ trong integration tracking; checkbox chỉ đóng sau khi merge và review.

## Phân công dự kiến

| Mã người | Thành viên hiện tại | Vai trò chính | Task chịu trách nhiệm chính |
|---|---|---|---|
| **P1** | **Huy** | Quản lý dự án, task, checkpoint, nghiệm thu và demo | T032, T047, T067–T071 |
| **P2** | **Tín** | Backend, API và tích hợp predictor | T019–T026, T030, T037–T038, T044–T045, T048–T050, T055, T060, T064, T066, T072–T073 |
| **P3** | **Cường** | MediaPipe pipeline, training model và model evaluation | T014–T017, T029, T033–T036, T054, T057–T059, T062, T065 |
| **P4** | **Quang** | Data crawler, data analysis, manifest và split | T008–T013, T018, T056, T061 |
| **P5** | **Hiển** | UX/UI và frontend | T027–T028, T031, T039–T043, T046, T051–T053, T074–T075; M1: T063 |

**Quy ước ownership**:

- Người chịu trách nhiệm chính cập nhật trạng thái task và bằng chứng kiểm thử; Huy theo dõi tiến độ,
  dependency và quyết định chuyển checkpoint.
- Task phối hợp vẫn có đúng một người chịu trách nhiệm chính. Người phối hợp được ghi trong mô tả hoặc
  khi cập nhật task, không tạo hai owner ngang nhau.
- T001–T012 đã hoàn thành trước khi chốt phân công theo tên; bảng trên chỉ gán lại các phần còn liên
  quan đến vận hành, không thay đổi lịch sử hoàn thành.
- Quang bàn giao manifest, quyền sử dụng, coverage và split; Cường là consumer và không tự thay đổi
  nhãn/split đã duyệt khi training.
- Cường chịu trách nhiệm toàn bộ chuỗi MediaPipe → GRU training → metrics → release metadata. Tín
  review khả năng load artifact và giữ predictor/API contract ổn định.
- Tín chịu trách nhiệm backend/API ở cả ba artifact kind; Hiển chỉ phụ thuộc OpenAPI/model-info, không
  phụ thuộc trực tiếp vào file model.
- Huy quyết định chuyển checkpoint. Fixture/pilot luôn `demoReady=false`; chỉ full model đủ 10 ý
  nghĩa và đạt gate mới được Huy duyệt làm model demo chính thức.
- P1–P5 là mã vị trí thành viên (`Person 1`–`Person 5`), không biểu thị độ ưu tiên và không liên quan
  đến `[P]` (parallel marker) hoặc priority của User Story.
- Hồ sơ tiến độ theo vai trò nằm trong `docs/team/`; `tasks.md` là nguồn sự thật cho checkbox hoàn
  thành, còn member file ghi trạng thái hằng ngày, blocker, bằng chứng và lịch sử bàn giao.

**Từ điển mã dùng trong task/plan**:

| Mã | Ý nghĩa |
|---|---|
| `Person P1`–`Person P5` | Mã người/vị trí thành viên; bảng phân công phía trên là nguồn chuẩn |
| `M0` | Hardening bắt buộc trước pilot; đã nhập vào task `T*` bên dưới |
| `M1` | Candidate cải thiện trước full/demo, chỉ mở khi trigger được Huy duyệt |
| `M2` | Candidate sau MVP; không thuộc backlog cam kết hiện tại |
| `US Priority P1/P2` | Độ ưu tiên User Story trong `spec.md` |
| `Vocabulary P0` | 10 ý nghĩa thuộc phạm vi MVP |
| `[P]` | Marker task có thể chạy song song |

Không dùng mã `VS-*` từ phản hồi senior làm backlog thứ hai. `tasks.md` vẫn là nguồn sự thật duy nhất.

**M0 coverage trong backlog hiện tại**:

| Lỗ hổng M0 | Task đã cập nhật | Owner / reviewer |
|---|---|---|
| WebM decode + timestamp | T014–T015, T049 | Person P3/Cường; Person P2/Tín review API boundary |
| Extractor/schema lock + train/serve parity | T014–T017, T037 | Person P3/Cường; Person P2/Tín review serving |
| Signer-only full quality gate | T018, T056–T058 | Person P4/Quang; Person P3/Cường consumer |
| Decode/busy stable errors | T021–T022, T026, T045, T049–T050 | Person P2/Tín |
| Fake-camera E2E | T032, T047 | Person P1/Huy; Person P5/Hiển review UX |
| Request correlation + optional diagnostics | T020, T023, T026–T027, T030, T038, T040, T045 | Person P2/Tín; Person P5/Hiển consumer |

**Milestone nội bộ cho T013** *(không tạo thêm owner hoặc task ID)*:

1. Quang đã đóng băng danh mục 10 Meaning tại `data/manifests/p0-meanings.csv`.
2. Quang hoàn tất inventory nguồn và license audit cho từng video.
3. Quang chốt tối đa 3 Meaning có coverage tốt nhất vào `pilot.csv` để bàn giao sớm cho Cường.
4. Quang tiếp tục lọc, bổ sung và phân tích coverage cho đủ 10 Meaning P0.
5. Quang đóng băng sample manifest `p0.csv`; Huy xác nhận checkpoint dữ liệu, Cường mới chạy full training.
6. T013 chỉ được đánh dấu hoàn thành ở milestone 5; milestone 3 đủ để kích hoạt pilot fallback.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể làm song song vì sửa file khác và không phụ thuộc task chưa hoàn thành.
- **[Story]**: Ánh xạ đến User Story trong `spec.md`.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Tạo cấu trúc monorepo và toolchain tối thiểu.

- [ ] T001 Tạo các thư mục nguồn theo `plan.md` gồm `apps/web/`, `services/inference-api/`, `ai/`, `data/`, `tests/` và `docs/`
- [ ] T002 [P] Khởi tạo Python 3.12 project và dependency groups cho API trong `services/inference-api/pyproject.toml`
- [ ] T003 [P] Khởi tạo Python 3.12 project và dependency groups cho AI trong `ai/pyproject.toml`
- [ ] T004 [P] Khởi tạo React TypeScript Vite app và test scripts trong `apps/web/package.json`
- [ ] T005 [P] Cấu hình Ruff, mypy và pytest dùng chung cho Python trong `pyproject.toml`
- [ ] T006 [P] Cấu hình ESLint, TypeScript type-check, Vitest và Playwright trong `apps/web/eslint.config.js`, `apps/web/tsconfig.json`, `apps/web/vite.config.ts` và `apps/web/playwright.config.ts`
- [ ] T007 Cập nhật `.gitignore` để loại raw video, processed artifacts, model binaries, file tạm và secret nhưng giữ manifest/metadata trong `.gitignore`
- [ ] T008 [P] Viết hướng dẫn đặt raw material ngoài repository và quy tắc quyền sử dụng trong `data/README.md`

**Checkpoint**: Cả ba project cài dependency, lint và chạy test rỗng thành công.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Contract dữ liệu, preprocessing và ranh giới API dùng chung cho mọi story, đồng thời mở
đường tích hợp bằng fixture mà không chờ full model.

**CRITICAL**: Full-model track không bắt đầu trước khi data foundation hoàn thành. Fixture integration
track MAY bắt đầu khi T019–T028 ổn định và không được trình bày là model demo-ready.

- [ ] T009 [P] Định nghĩa `Meaning`, `SignClass` và enum metadata theo các constraint trong `data-model.md` tại `ai/src/visign_ai/dataset/entities.py`
- [ ] T010 [P] Định nghĩa schema hàng manifest gồm `sampleId` duy nhất, `recordingSessionId` bắt buộc, `licenseStatus`, `verificationStatus` và split tại `ai/src/visign_ai/dataset/manifest_schema.py`
- [ ] T011 [P] Viết unit tests cho duplicate ID, license không approved, rejected sample và signer/session leakage tại `ai/tests/dataset/test_manifest_validation.py`
- [ ] T012 Cài manifest validator và báo cáo coverage theo class/signer tại `ai/src/visign_ai/dataset/validate_manifest.py`
- [ ] T013 Dùng danh mục đã chốt tại `data/manifests/p0-meanings.csv`, tạo sớm `data/manifests/pilot.csv` với tối đa 3 Meaning có video đã duyệt rồi hoàn thiện sample manifest `data/manifests/p0.csv` phủ đúng 10 Meaning P0 sau audit raw material
- [ ] T014 [P] Viết decoder/extractor tests cho WebM Chrome/Edge fixture, PTS tăng dần, corrupt clip, output shape, missing mask và golden clip→tensor parity tại `ai/tests/landmarks/test_video_pipeline.py`
- [ ] T015 Cài `VideoDecoder` dùng PyAV sau spike gate và MediaPipe video adapter với pinned `extractorVersion` tại `ai/src/visign_ai/landmarks/video_decoder.py` và `ai/src/visign_ai/landmarks/holistic_extractor.py`
- [ ] T016 Cài versioned `feature_schema.json`, chuẩn hóa tọa độ, resampling và missing-landmark mask dùng chung train/API tại `ai/src/visign_ai/landmarks/sequence_transform.py` và `ai/configs/feature_schema.json`
- [ ] T017 Cài CLI trích xuất toàn manifest, ghi extractor/schema version và stable decode/extraction rejection code tại `ai/src/visign_ai/landmarks/extract_manifest.py`
- [ ] T018 Cài signer-held-out split cho full gate; chỉ cho phép session-only split ở pilot/dev với nhãn audit cấm unseen-signer claim tại `ai/src/visign_ai/dataset/create_splits.py`
- [ ] T019 [P] Định nghĩa model metadata cho `fixture|pilot|full`, extractor/feature schema version, nullable fixture accuracy/precision/recall/Macro-F1 và gate `full && 10 meanings && macroF1 >= 0.80 && mọi perMeaningRecall >= 0.65` tại `services/inference-api/src/visign_api/domain/model_version.py`
- [ ] T020 [P] Định nghĩa prediction request/accepted/rejected/error states không thể kết hợp sai; success response giữ `processingTimeMs` và optional `timingsMs {decode,extract,infer}` plus `qualityHints {handsDetectedRatio,frameCount}` không chứa landmark tại `services/inference-api/src/visign_api/domain/prediction.py`
- [ ] T021 [P] Cài error catalog ổn định gồm `CLIP_DECODE_FAILED` và `SERVICE_BUSY` đúng `contracts/openapi.yaml` tại `services/inference-api/src/visign_api/domain/errors.py`
- [ ] T022 Cài cấu hình model path, MIME allowlist, byte/duration limit, inference wait timeout và CORS tại `services/inference-api/src/visign_api/config.py`
- [ ] T023 Cài structured logging không persist payload gồm request ID, model version, total/per-stage duration, accepted và error code tại `services/inference-api/src/visign_api/observability.py`
- [ ] T024 Cài temporary-clip boundary luôn xóa file trong success/failure tại `services/inference-api/src/visign_api/inference/temporary_clip.py`
- [ ] T025 [P] Viết unit tests chứng minh temporary clip bị xóa ở mọi đường đi tại `services/inference-api/tests/unit/test_temporary_clip.py`
- [ ] T026 Cài FastAPI app, versioned router, `X-Request-ID` receive/generate/echo middleware, bounded single-inference coordinator và exception mapping tại `services/inference-api/src/visign_api/main.py` và `services/inference-api/src/visign_api/api/router.py`
- [ ] T027 [P] Định nghĩa TypeScript API types tối thiểu bám `contracts/openapi.yaml`, giữ `X-Request-ID`, optional prediction diagnostics, `artifactKind`, `extractorVersion`, `featureSchemaVersion`, actual meanings và nullable fixture metrics tại `apps/web/src/types/inference-api.ts`; tự động sinh type bằng `openapi-typescript` thuộc M1
- [ ] T028 [P] Tạo Vietnamese UI copy, disclaimer và accessible labels tại `apps/web/src/content/vi.ts`

**Checkpoint**: Manifest có thể audit; cùng feature schema được dùng cho training và serving; API app khởi động nhưng chưa cần model thật.

---

## Phase 3: User Story 1 - Nhận diện một ký hiệu (Priority: P1) — MVP

**Goal**: Camera → đoạn ký hiệu → API → model → chữ tiếng Việt và độ tin cậy.

**Independent Test**: Dùng model fixture có một ký hiệu hợp lệ, ghi/gửi clip camera và nhận response
đúng contract với `accepted=true`, chữ tiếng Việt và model version trong không quá 3 giây.

### Tests for User Story 1

- [ ] T029 [P] [US1] Viết model shape, packed-sequence, deterministic forward và class-subset tests dùng chung cho pilot/full tại `ai/tests/training/test_gru_classifier.py`
- [ ] T030 [P] [US1] Tạo deterministic fixture artifact và viết contract tests chứng minh fixture/pilot/full dùng cùng accepted response schema, echo/generated `X-Request-ID`, non-negative optional timings và bounded quality hints tại `services/inference-api/tests/fixtures/model-artifacts/fixture/` và `services/inference-api/tests/contract/test_predictions_contract.py`
- [ ] T031 [P] [US1] Viết component tests cho permission, recording và accepted result tại `apps/web/tests/recognition/recognition-flow.test.tsx`
- [ ] T032 [P] [US1] Viết E2E happy path bằng Chromium fake-camera Y4M và fixture predictor, không thay camera flow bằng HTTP-only mock, tại `tests/e2e/recognition-happy-path.spec.ts`

### Implementation for User Story 1

- [ ] T033 [US1] Cài GRU classifier nhận padded landmark sequence tại `ai/src/visign_ai/training/gru_classifier.py`
- [ ] T034 [US1] Cài dataset loader và batching giữ label order ổn định tại `ai/src/visign_ai/training/sequence_dataset.py`
- [ ] T035 [US1] Tạo cấu hình seed tái lập cho pilot tối đa 3 từ và full 10 từ tại `ai/configs/pilot-gru.yaml` và `ai/configs/p0-gru.yaml`
- [ ] T036 [US1] Cài training CLI nhận class subset và lưu artifact metadata bất biến gồm `artifactKind`, dataset/feature schema/class map tại `ai/src/visign_ai/training/train.py`
- [ ] T037 [US1] Cài predictor interface với deterministic fixture và pilot/full adapter qua `MODEL_ARTIFACT_PATH`; kiểm tra extractor/feature schema và fail closed để rollback tại `services/inference-api/src/visign_api/inference/predictor.py`
- [ ] T038 [US1] Cài `POST /api/v1/predictions` cho accepted result với total/per-stage timings và quality hints không chứa frame/landmark tại `services/inference-api/src/visign_api/api/predictions.py`
- [ ] T039 [P] [US1] Cài camera permission, preview và start/stop/cancel recording tại `apps/web/src/features/recognition/CameraRecorder.tsx`
- [ ] T040 [P] [US1] Cài typed API client gửi camera blob, truyền/đọc `X-Request-ID`, đọc model-info và bỏ qua an toàn optional diagnostics khi không có tại `apps/web/src/services/inferenceApi.ts`
- [ ] T041 [US1] Cài recognition state machine cho idle/permission/recording/submitting/result và loaded artifact kind tại `apps/web/src/features/recognition/useRecognition.ts`
- [ ] T042 [US1] Cài accepted result view gồm tiếng Việt, confidence, disclaimer và cảnh báo integration/pilot khi `demoReady=false` tại `apps/web/src/features/recognition/RecognitionResult.tsx`
- [ ] T043 [US1] Ghép luồng camera, model-info và prediction vào trang chính mà không rẽ nhánh endpoint theo artifact tại `apps/web/src/App.tsx`

**Checkpoint**: US1 chạy độc lập với model fixture và có thể demo happy path.

---

## Phase 4: User Story 2 - Từ chối kết quả không chắc chắn (Priority: P1)

**Goal**: Không đoán bắt buộc; xử lý low confidence, clip lỗi, camera lỗi và service lỗi an toàn.

**Independent Test**: Gửi fixture low-confidence, no-person, clip sai và từ chối camera; mỗi trường hợp
hiển thị đúng rejected/error state, không hiển thị một từ như kết quả chắc chắn và cho phép thử lại.

### Tests for User Story 2

- [ ] T044 [P] [US2] Viết unit tests cho threshold boundary và accepted/rejected decision tại `services/inference-api/tests/unit/test_prediction_decision.py`
- [ ] T045 [P] [US2] Mở rộng contract tests cho 400, 413, 415, `CLIP_DECODE_FAILED`, `SERVICE_BUSY` với optional `Retry-After`, model-not-ready 503, `PREDICTION_FAILED` 500 không lộ exception, low-confidence HTTP 200 và `X-Request-ID` trên mọi response tại `services/inference-api/tests/contract/test_predictions_contract.py`
- [ ] T046 [P] [US2] Viết web tests cho denied permission, cancel, retry, rejected và service unavailable tại `apps/web/tests/recognition/recognition-errors.test.tsx`
- [ ] T047 [P] [US2] Viết E2E permission-denied, corrupt clip, service-busy, low-confidence và retry flows bằng fake-camera/control fixture tại `tests/e2e/recognition-negative-paths.spec.ts`

### Implementation for User Story 2

- [ ] T048 [US2] Cài pure confidence decision trả accepted hoặc “Không nhận diện được” tại `services/inference-api/src/visign_api/inference/prediction_decision.py`
- [ ] T049 [US2] Cài clip validation cho MIME, byte limit, WebM magic bytes, decoder probe, PTS duration, person và landmark sufficiency tại `services/inference-api/src/visign_api/inference/clip_validator.py`
- [ ] T050 [US2] Hoàn thiện error mapping và cleanup cho prediction endpoint tại `services/inference-api/src/visign_api/api/predictions.py`
- [ ] T051 [US2] Cài rejected result và retry action tại `apps/web/src/features/recognition/RecognitionResult.tsx`
- [ ] T052 [US2] Cài camera/API error presentation với thông báo tiếng Việt ổn định tại `apps/web/src/features/recognition/RecognitionError.tsx`
- [ ] T053 [US2] Cài timeout, cancel request và reset state tại `apps/web/src/features/recognition/useRecognition.ts`

**Checkpoint**: US1 và US2 đều chạy; mọi low-confidence/invalid input fail closed.

---

## Phase 5: User Story 3 - Đánh giá chất lượng bản MVP (Priority: P2)

**Goal**: Model release có thể truy về dữ liệu, split và metrics; evaluator xác minh được demo gate.

**Independent Test**: Chạy evaluation trên test split rồi kiểm tra report/model-info chứa dataset version,
10 meanings, accuracy, precision/recall từng meaning, Macro-F1, confusion matrix, latency, signer-held-out
provenance và `demoReady` đúng gate.

### Tests for User Story 3

- [ ] T054 [P] [US3] Viết evaluation metric tests và chứng minh fixture/pilot không thể qua full demo gate tại `ai/tests/evaluation/test_model_gate.py`
- [ ] T055 [P] [US3] Viết `GET /health` và `GET /model-info` contract tests cho fixture/pilot/full, `extractorVersion`, `featureSchemaVersion`, actual meanings và nullable metrics tại `services/inference-api/tests/contract/test_model_info_contract.py`
- [ ] T056 [P] [US3] Viết split regression tests chứng minh full test không trùng signer và session-only split không thể mang nhãn unseen-signer tại `ai/tests/dataset/test_split_audit.py`

### Implementation for User Story 3

- [ ] T057 [US3] Cài accuracy, Macro-F1, per-meaning precision/recall, confusion matrix, signer/sample counts và latency evaluation tại `ai/src/visign_ai/evaluation/metrics.py`
- [ ] T058 [US3] Cài evaluation CLI sinh JSON metrics, confusion-matrix image và signer-held-out split provenance tại `ai/src/visign_ai/evaluation/evaluate.py`
- [ ] T059 [US3] Cài metadata writer cho mọi artifact và release gate chỉ chấp nhận full 10-meaning signer-held-out model tại `ai/src/visign_ai/evaluation/release_gate.py`
- [ ] T060 [US3] Cài `GET /api/v1/health` và `GET /api/v1/model-info` công bố artifact kind, extractor/feature schema version, actual meanings và readiness tại `services/inference-api/src/visign_api/api/system.py`
- [ ] T061 [P] [US3] Viết dataset card từ manifest audit tại `docs/dataset-card.md`
- [ ] T062 [P] [US3] Viết model card gồm artifact kind, supported meanings, accuracy, per-meaning precision/recall, Macro-F1, confusion matrix, latency, signer-held-out result, limitations, fallback status và safety disclaimer tại `docs/model-card.md`

**Checkpoint**: Chỉ model đạt đủ gate mới được API tải làm model demo.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Kiểm chứng toàn hệ thống và chuẩn bị demo.

- [ ] T064 [P] Thêm integration test camera clip → cleanup → predictor → response cho fixture/pilot/full và artifact swap tại `tests/integration/test_prediction_pipeline.py`
- [ ] T065 Chạy performance benchmark và ghi p50/p95 processing time trên laptop demo tại `ai/src/visign_ai/evaluation/benchmark_inference.py` và `docs/model-card.md`
- [ ] T066 Audit privacy để chứng minh không có video/frame/PII trong log hoặc artifact tại `tests/integration/test_prediction_privacy.py`
- [ ] T067 Chạy toàn bộ kịch bản gồm fallback/swap/rollback trong `specs/001-vsl-recognition-mvp/quickstart.md` và lưu kết quả vào `docs/verification-report.md`
- [ ] T068 [P] Viết demo script full và kịch bản pilot giới hạn không tuyên bố demo-ready tại `docs/demo-script.md`
- [ ] T069 [P] Viết hướng dẫn cài đặt, chạy local, artifact switching/rollback, cấu trúc project và giới hạn MVP tại `README.md`
- [ ] T070 Tổng duyệt demo trên laptop đích và ghi camera/browser/model versions, artifact kind và demoReady tại `docs/demo-rehearsal.md`
- [ ] T071 Thực hiện kiểm thử hoàn thành tác vụ lần đầu với ít nhất 10 người và ghi tỷ lệ thành công vào `docs/usability-report.md`

---

## Phase 7: User Story 2 HTTP Routing Follow-up

**Goal**: Chuẩn hóa lỗi route/method và trailing-slash redirect để frontend không hiển thị raw
framework message hoặc gửi lại video ngoài ý muốn.

**Independent Test**: Gọi unknown route, sai method và canonical route có trailing slash với redirect
disabled; xác nhận status/error envelope/header đúng, sau đó mô phỏng các response đó ở frontend và
kiểm tra stable Vietnamese copy, không auto-resubmit và không lộ raw server text.

- [ ] T072 [P] [US2] Viết backend contract tests cho `404 ROUTE_NOT_FOUND`, `405 METHOD_NOT_ALLOWED`, `307` giữ method/body/`Location`, `X-Request-ID`, cùng hành vi chưa bật `403`/`304` tại `services/inference-api/tests/contract/test_http_routing_contract.py`
- [ ] T073 [US2] Cài stable error catalog và exception handlers cho 404/405, giữ `Allow`/`Location`/`X-Request-ID`, document 404/405/307 và giữ health `Cache-Control: no-store` tại `services/inference-api/src/visign_api/domain/errors.py`, `services/inference-api/src/visign_api/main.py` và `contracts/openapi.yaml`
- [ ] T074 [P] [US2] Viết frontend transport/component tests cho 404/405, canonical URL, không auto-resubmit và không render raw server text tại `apps/web/tests/services/inferenceApi.test.ts` và `apps/web/tests/recognition/recognition-errors.test.tsx`
- [ ] T075 [US2] Thêm typed API compatibility errors và stable Vietnamese placeholders; reserve 403/304 nhưng không trình bày là trạng thái MVP đang hoạt động tại `apps/web/src/services/inferenceApi.ts`, `apps/web/src/content/vi.ts` và `apps/web/src/features/recognition/RecognitionError.tsx`

**Checkpoint**: Backend và frontend cùng tuân theo `docs/team/backend-http-status-contract.md` và
`docs/team/frontend-http-status-placeholders.md`; US1 prediction success flow không thay đổi.

---

## M1 Candidates — Không thuộc MVP commitment

Các mục dưới đây chỉ được mở khi Huy ghi trigger, owner và acceptance evidence. Chúng không chặn
`demoReady`, không nằm trên critical path và không được tính vào số task MVP còn lại.

- [ ] T063 [P] Chạy accessibility audit chuyên sâu cho keyboard, focus, status announcements **[M1 candidate]**
  và camera labels trong `apps/web/tests/accessibility/recognition-accessibility.spec.ts`. **Trigger**:
  MVP camera flow ổn định hoặc có yêu cầu nghiệm thu accessibility riêng. Basic labels và semantic
  states vẫn thuộc T028/T039–T053 của MVP.
- **M1-API-01 [P]**: Tự động sinh và kiểm tra drift TypeScript API types bằng `openapi-typescript` từ
  `specs/001-vsl-recognition-mvp/contracts/openapi.yaml`. **Trigger**: contract thay đổi thường xuyên,
  có client thứ hai hoặc lỗi drift thủ công xuất hiện. T027 vẫn cung cấp type tối thiểu cho MVP.

## M2 Candidates — Không thuộc backlog hiện tại

Không có task `T*` hiện tại cần chuyển sang M2. Endpoint landmark JSON, client-side extraction,
ONNX, DVC/MLflow, cloud và mở rộng vocabulary tiếp tục chỉ là decision backlog trong `plan.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: Bắt đầu ngay.
- **Phase 2 / Integration track**: T019–T028 có thể hoàn thành với fixture contract, không phụ thuộc
  T013 hoặc full training.
- **Phase 2 / Data-model track**: Quang bàn giao pilot subset trong T013 để mở pilot; full track chờ
  `p0.csv` đúng 10 meanings và T018 split audit.
- **M0 gate**: Pilot dùng model thật chỉ mở sau khi T014–T017 chứng minh decoder/extractor/schema parity;
  fixture integration vẫn được phép chạy song song.
- **US1 / Fixture**: Bắt đầu sau integration foundation và model fixture; tạo luồng giá trị đầu tiên.
- **US1 / Pilot-Full**: Cường cần T013 pilot/full manifest, T014–T018 preprocessing/split và giữ cùng
  artifact contract đã dùng cho fixture.
- **US2**: Phụ thuộc prediction states/API shell của Phase 2; có thể bắt đầu song song phần lớn với US1.
- **US3**: Phụ thuộc manifest/split/model metadata của Phase 2; evaluation có thể song song với UI US1.
- **Phase 6**: Phụ thuộc các story được chọn cho demo; T070 phụ thuộc toàn bộ cổng bắt buộc.

### User Story Dependencies

```text
Setup -> Foundation -> US1 -> Integration/Polish
                    \-> US2 -/
                    \-> US3 -/
```

- **US1** không phụ thuộc data/full training để chạy happy path với fixture.
- **US2** dùng endpoint và state model chung nhưng kiểm thử được độc lập bằng low-confidence fixture.
- **US3** dùng model artifact chung nhưng kiểm thử được độc lập bằng metrics fixture.
- Fixture/pilot/full dùng cùng contract; nâng cấp hoặc rollback artifact không tạo một user story hay
  frontend branch riêng.

### Parallel Opportunities

- T002–T004, T005–T006 và T008 có thể chia cho backend/AI/frontend.
- T009–T011, T014, T019–T021, T025, T027–T028 sửa các vùng độc lập.
- Sau integration foundation, Tín làm T030/T037–T038, Hiển làm T031/T039–T043 và Huy làm T032 bằng
  fixture; không chờ Quang hoặc Cường hoàn thành full track.
- Quang làm T013/T018/T056/T061 trong khi Cường làm T014–T017 rồi T029/T033–T036/T054/T057–T059.
- Trong US2, Tín làm T044–T045/T048–T050, Hiển làm T046/T051–T053 và Huy làm T047.
- US2 tests T044–T047 và US3 tests T054–T056 có thể chạy song song.
- T061–T062 và T068–T069 là các tài liệu độc lập sau khi contract ổn định; T063 chỉ mở theo trigger M1.

## Parallel Example: User Story 1

```text
Cường/AI: T029 -> T033 -> T034 -> T035 -> T036
Tín/API:  T030 -> T037 -> T038
Hiển:     T031 -> T039 + T040 -> T041 -> T042 -> T043
Huy:      T032, sau đó điều phối kiểm tra luồng tích hợp
Quang:    T013 pilot subset -> T018, tiếp tục hoàn thiện full manifest
```

## Implementation Strategy

### MVP First

1. Hoàn thành integration foundation và dùng fixture cho camera → API → UI, kể cả US2 fail-closed.
2. Chạy M0 decoder/extractor/schema gate và khóa golden clip→tensor parity trên laptop demo.
3. Quang bàn giao pilot subset tối đa 3 meanings; Cường train/evaluate pilot bằng đúng pipeline full.
4. Tín đổi artifact qua `MODEL_ARTIFACT_PATH`; Hiển xác nhận model-info/pilot notice, Huy chạy smoke.
5. Quang hoàn thiện signer-held-out 10-meaning manifest/split; Cường train/evaluate full và ghi release metadata.
6. Huy chỉ mở candidate M1 khi trigger/evidence được ghi; M2 nằm ngoài MVP commitment.
7. Chỉ full model đạt gate mới được Huy duyệt `demoReady=true`; nếu lỗi thì rollback artifact trước.

### Team 5 người

- **P1 / Huy — Project/Task Manager**: quản lý scope, backlog, dependency, fallback trigger, checkpoint,
  nghiệm thu, E2E và demo; không sở hữu implementation FE/BE/model.
- **P2 / Tín — Backend/API**: sở hữu domain/API, predictor integration, artifact configuration, cleanup,
  contract/integration tests, privacy và rollback vận hành.
- **P3 / Cường — Training Models**: sở hữu MediaPipe extraction/preprocessing, GRU pilot/full training,
  evaluation, release metadata, model card và performance benchmark.
- **P4 / Quang — Data Crawler/Data Analyst**: sở hữu nguồn/quyền sử dụng, lọc nhãn, pilot/full manifest,
  coverage, split leakage audit và dataset card.
- **P5 / Hiển — UX/UI/Frontend**: thiết kế trải nghiệm camera, trạng thái nhận diện, lỗi, accessibility và
  triển khai React frontend, gồm notice cho fixture/pilot dựa trên model-info.

## Notes

- Danh mục P0 đã chốt; T013 vẫn phụ thuộc việc lọc, bổ sung raw material và audit nguồn/quyền sử dụng
  trước khi tạo sample manifest cho pilot/full.
- Fixture mở khóa FE/BE/E2E nhưng không phải bằng chứng chất lượng model; pilot chỉ là smoke model và
  không được đổi thành `demoReady=true`.
- Chuyển artifact phải giữ nguyên API contract, kiểm tra feature schema và có đường rollback về
  artifact smoke-tested gần nhất.
- Không commit raw video, model binary hoặc dữ liệu không rõ quyền sử dụng.
- Không mở rộng lên 30 từ trước khi 10 từ P0 đạt cổng chất lượng.
- M1/M2 trong `plan.md` là decision backlog, không phải checkbox cam kết; chỉ `T*` trong file này là task.
- Ngoại lệ có chủ đích: T063 được giữ mã lịch sử nhưng đặt dưới M1, nên không tính vào backlog MVP.
- Không commit thay đổi nếu người dùng chưa yêu cầu.
