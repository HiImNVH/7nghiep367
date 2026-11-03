# Implementation Plan: ViSign VSL Recognition MVP

**Branch**: `001-vsl-recognition-mvp` | **Date**: 2026-10-19 | **Updated**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-vsl-recognition-mvp/spec.md`

## Summary

ViSign MVP nhận diện một trong 10 ý nghĩa VSL P0 từ một đoạn camera do người dùng chủ động bắt đầu và
kết thúc, sau đó trả chữ tiếng Việt, độ tin cậy và trạng thái chấp nhận. Video raw material chỉ dùng
cho huấn luyện và đánh giá. Pipeline trích xuất landmark bàn tay, tư thế và khuôn mặt bằng MediaPipe,
chuẩn hóa chuỗi và phân loại bằng GRU. Một web app React gửi đoạn camera ngắn đến FastAPI; API xử lý
tạm thời trong bộ nhớ/thư mục tạm, trả kết quả rồi xóa đầu vào.

## Technical Context

**Language/Version**: Python 3.12 cho AI/API; TypeScript với Node.js 22.12+ cho web

**Primary Dependencies**: MediaPipe Tasks Holistic Landmarker, PyAV decoder behind a `VideoDecoder`
boundary, PyTorch GRU, FastAPI/Pydantic, React + Vite

**Storage**: File-based cho MVP: CSV manifest, JSON label map/model metadata, model artifact; không có
cơ sở dữ liệu và không lưu video dự đoán của người dùng

**Testing**: pytest + FastAPI TestClient cho Python; golden clip→tensor parity tests; Vitest cho web
unit; Playwright với fake-camera Y4M cho E2E; script đánh giá xuất confusion matrix, macro-F1,
recall từng lớp, negative/OOD false-accept report và latency từng stage

**Target Platform**: Windows 11 chạy cục bộ trên laptop demo; trình duyệt Chromium hiện đại có camera

**Project Type**: Web application gồm frontend, inference API và pipeline AI ngoại tuyến

**Performance Goals**: 95% lần thử hợp lệ trả kết quả hoặc lỗi có thể xử lý trong 3 giây sau khi gửi;
camera preview phản hồi liên tục; API chỉ xử lý một yêu cầu dự đoán tại một thời điểm trong MVP

**Constraints**: 10 ý nghĩa P0; ký hiệu riêng lẻ; camera là đầu vào dự đoán duy nhất; không lưu video
người dùng; Macro-F1 ≥80%; recall mỗi ý nghĩa ≥65%; ưu tiên ổn định demo cục bộ

**Scale/Scope**: Một nhóm 5 thành viên, một máy demo, 10 ý nghĩa P0, khoảng 10–20 lớp nếu có biến thể.
Mức 20–30 mẫu được duyệt mỗi lớp và 3–5 signer là planning floor cho pilot, không phải quality gate;
full track chỉ mở khi coverage theo meaning × signer và signer-held-out split đủ để đánh giá trung thực.

**Frozen P0 Vocabulary**: `GIAY_TO` — Giấy tờ (giấy); `DAU_BUNG` — Đau bụng; `THUOC` — Thuốc;
`SOT` — Sốt; `NHAN` — Nhận; `BAN` — Bạn (Ngôi thứ 2); `XIN_CHAO` — Xin chào; `CAM_ON` — Cảm ơn;
`CHO` — Chờ (đợi); `SAO_CHEP` — Sao chép. Registry chuẩn nằm tại
`data/manifests/p0-meanings.csv`; manifest video chỉ được tạo từ mẫu đã qua audit.

**Team Ownership**: P1/Huy quản lý dự án, task, checkpoint và nghiệm thu; P2/Tín phụ trách backend,
API và tích hợp predictor; P3/Cường phụ trách MediaPipe pipeline, GRU training, model evaluation và
benchmark; P4/Quang phụ trách data crawling, data analysis, manifest và split; P5/Hiển phụ trách
UX/UI và frontend. P1–P5 là mã người, không phải độ ưu tiên. Mỗi task có một owner theo chuyên môn;
các điểm giao contract có reviewer được ghi trong `tasks.md`.

## Quy ước mã không nhập nhằng

| Mã | Ý nghĩa | Ví dụ | Không có nghĩa |
|---|---|---|---|
| `Person P1`–`Person P5` | Vị trí thành viên ổn định | `Person P2 / Tín` | Không phải mức ưu tiên |
| `M0` | Thay đổi bắt buộc để đóng lỗ hổng MVP trước pilot | decoder, parity, signer split | Không phải mã người |
| `M1` | Cải thiện phải đánh giá trước full/demo; chỉ triển khai khi trigger xảy ra | OOD strategy, checksum, latency | Không tự động là task đã cam kết |
| `M2` | Nâng cấp sau MVP hoặc chỉ làm khi benchmark/scope mới yêu cầu | ONNX, DVC, cloud | Không thuộc critical path MVP |
| `US Priority P1/P2` | Độ ưu tiên User Story trong `spec.md` | US1 là P1 | Không phải Person ID |
| `Vocabulary P0` | 10 ý nghĩa thuộc phạm vi từ vựng MVP | `XIN_CHAO` | Không phải M0 hoặc Person P0 |
| `[P]` | Task có thể làm song song | `T014 [P]` | Không phải priority/person |

`tasks.md` là backlog duy nhất. Mã `VS-*` trong phản hồi senior chỉ là proposal reference; một đề xuất
chỉ trở thành cam kết khi đã được ánh xạ vào task `T*` hoặc được Huy duyệt thành task mới.

## MVP Hardening theo M0/M1/M2

### M0 — áp dụng vào plan hiện tại

1. Tách `VideoDecoder` khỏi MediaPipe extractor; PyAV là implementation chính nếu spike clip thật
   Chrome/Edge trên laptop demo đạt tiêu chí decode, timestamp và duration.
2. Chốt MediaPipe/extractor version, hash model bundle và feature schema trước bulk extraction.
3. Dùng duy nhất package `visign_ai.landmarks` cho train/API; golden clip→tensor test cưỡng chế parity.
4. Full quality gate bắt buộc signer-held-out split; session-only split chỉ có giá trị pilot/dev.
5. Kiểm tra MIME, byte limit, WebM magic bytes và decoder probe; phân biệt `CLIP_DECODE_FAILED`.
6. Một inference slot có timeout; request đến khi bận nhận `SERVICE_BUSY` và retry guidance.
7. E2E camera dùng Y4M fixture và permission control thay vì chỉ mock HTTP.
8. Mọi response echo `X-Request-ID`; prediction có thể trả `timingsMs` và `qualityHints` không chứa
   frame/landmark, không persist và không tham gia quyết định `accepted`.

### M1 — candidate improvements trước full/demo

| Cải thiện | Trigger | Bằng chứng quyết định |
|---|---|---|
| Threshold + top1/top2 margin + temperature scaling | Baseline còn false accept hoặc confidence lệch | So sánh cùng validation/OOD split; không giảm recall P0 quá mức đã duyệt |
| Lớp `NONE` | Threshold/margin chưa đủ tốt và Quang có negative set đa dạng | A/B với baseline 10 lớp; `NONE` không tính vào Macro-F1 10 meaning |
| Artifact SHA-256, config hash, warm-up | Trước khi cho phép swap/rollback full artifact | Artifact sai hash/schema fail closed; request đầu không chịu cold-start bất thường |
| Bootstrap/uncertainty report | Test set đủ signer để ước lượng có ý nghĩa | Báo sample/signer count và interval, không dùng interval thay gate hiện có |
| Local quality command và CI | Repository Git/remote sẵn sàng | Lint, type, unit, contract, web và E2E fixture chạy lặp lại |
| OpenAPI TypeScript code generation | Contract đổi thường xuyên, có client thứ hai hoặc xuất hiện type drift | Generated types khớp schema và drift check fail khi contract/client lệch |
| Accessibility audit chuyên sâu | Camera flow đã ổn định hoặc có yêu cầu nghiệm thu riêng | Keyboard, focus, status announcement và camera labels đạt audit; basic accessibility vẫn ở M0 |

### M2 — ghi nhận, chưa đưa vào MVP commitment

- DVC/MLflow hoặc TensorBoard cho versioning/experiment tracking nâng cao.
- BiGRU+attention, TCN; Transformer/ST-GCN chỉ khi quy mô dữ liệu tăng đáng kể.
- ONNX Runtime chỉ khi benchmark PyTorch không đạt latency gate và parity test đạt.
- Browser MediaPipe overlay, client-side landmark extraction và endpoint landmark JSON.
- Tailwind/shadcn, Docker, cloud hosting, consent-based data collection và mở rộng thêm 20 meaning.

M1/M2 không được thêm vào sprint chỉ vì xuất hiện trong plan. Huy phải ghi trigger, owner, acceptance
evidence và ảnh hưởng scope trước khi đổi trạng thái thành task cam kết.

## Luồng dữ liệu M0

```text
Camera WebM
  -> upload limits + temporary file
  -> VideoDecoder (container/codec probe, frame PTS)
  -> HolisticExtractor (pinned extractorVersion)
  -> SequenceTransform (featureSchemaVersion)
  -> Predictor (fixture | pilot | full)
  -> decision rule
  -> PredictionResponse
  -> delete temporary file in finally
```

Training CLI và inference API phải gọi cùng `HolisticExtractor` và `SequenceTransform`; không được
fork preprocessing riêng ở service layer.

## Fallback khi full model train quá hạn

Ba artifact dùng cùng `featureSchemaVersion`, predictor interface và response contract:

| Cấp | Mục đích | Dữ liệu/lớp | Quy tắc phát hành |
|---|---|---|---|
| `fixture` | Mở khóa contract, frontend, backend và E2E | Predictor test double trả kết quả xác định trước; không phải model học máy | Luôn `demoReady=false`; chỉ dùng local/test |
| `pilot` | Smoke-test MediaPipe → GRU → API bằng dữ liệu thật | Tối đa 3 ý nghĩa có coverage tốt nhất; ưu tiên đủ ba nhóm nếu khả thi | Luôn `demoReady=false`; UI phải ghi rõ phạm vi giới hạn |
| `full` | Model MVP chính thức | Đúng 10 ý nghĩa P0 đã đóng băng | Chỉ `demoReady=true` khi đạt mọi gate |

### Trigger và chuyển cấp

1. Tín và Hiển tích hợp bằng `fixture` ngay khi contract ổn định, không chờ raw material hoặc train.
2. Nếu manifest/split đầy đủ chưa sẵn sàng tại checkpoint tích hợp nội bộ, Quang bàn giao subset tối
   đa 3 ý nghĩa đã duyệt để Cường train `pilot`.
3. Cường đóng gói mọi artifact với metadata bất biến gồm `artifactKind`, `modelVersion`,
   `datasetVersion`, `featureSchemaVersion`, `classLabels`, `meaningMap` và `demoReady`.
4. Tín chọn artifact bằng `MODEL_ARTIFACT_PATH`; đổi từ fixture → pilot → full không đổi endpoint hoặc
   response prediction. API được restart và chạy contract/smoke tests trước khi nhận traffic demo.
5. Hiển đọc `/api/v1/model-info`; khi `demoReady=false`, giao diện hiển thị rõ chế độ tích hợp/pilot và
   danh sách ý nghĩa thực sự hỗ trợ.
6. Huy chỉ duyệt demo MVP chính thức với `full`. Nếu đến hạn chỉ có pilot, nhóm chỉ trình bày đó là
   bản tích hợp giới hạn, không tuyên bố đã đạt quality gate 10 ý nghĩa.

Fixture chỉ thay phần suy luận học máy phía sau predictor interface; nó không được bỏ qua MIME/size,
temporary-file cleanup, error mapping, privacy hoặc API contract. Những kiểm tra cần landmark thật
được bật với pilot/full và có test riêng, nên fixture không được dùng làm bằng chứng cho model quality.

### Rollback

Giữ đường dẫn artifact đã vượt smoke test gần nhất. Nếu artifact mới lỗi schema, load, latency hoặc
contract, Tín khôi phục `MODEL_ARTIFACT_PATH` về artifact trước, restart API và chạy lại health,
model-info, prediction smoke test. Video người dùng vẫn phải bị xóa ở mọi cấp.

## Constitution Check

*GATE: PASS trước Phase 0 và PASS lại sau Phase 1.*

| Gate | Evidence | Status |
|------|----------|--------|
| An toàn và trung thực | API có `accepted`; UI có “Không nhận diện được” và disclaimer | PASS |
| Nguồn gốc dữ liệu | Manifest bắt buộc source, license, region, verified, signer/session | PASS |
| Chất lượng đo được | Split theo người, macro-F1, per-class recall, confusion matrix, latency | PASS |
| Quyền riêng tư | Request video chỉ tồn tại tạm thời và bị xóa sau xử lý | PASS |
| MVP chạy xuyên suốt | Chỉ 10 từ, camera → API → model → chữ; candidate M1/M2 không tự vào sprint | PASS |
| Kiểm thử bắt buộc | Unit, contract, integration, E2E và model evaluation đều có cổng | PASS |
| Fallback không gây hiểu nhầm | Fixture/pilot luôn `demoReady=false`; UI công bố đúng phạm vi | PASS |

Không có ngoại lệ hiến pháp cần biện minh.

## Project Structure

### Documentation (this feature)

```text
specs/001-vsl-recognition-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
apps/
└── web/
    ├── src/
    │   ├── components/
    │   ├── features/recognition/
    │   ├── services/
    │   └── types/
    └── tests/

services/
└── inference-api/
    ├── src/visign_api/
    │   ├── api/
    │   ├── domain/
    │   ├── inference/
    │   └── main.py
    └── tests/
        └── fixtures/model-artifacts/fixture/

ai/
├── src/visign_ai/
│   ├── dataset/
│   ├── landmarks/
│   ├── training/
│   └── evaluation/
├── configs/
├── models/
└── tests/

data/
├── manifests/
├── processed/
└── README.md

tests/
├── contract/
├── integration/
└── e2e/

docs/
├── dataset-card.md
├── model-card.md
├── demo-script.md
└── team/
    ├── README.md
    ├── member-template.md
    ├── project-manager.md
    ├── backend-api.md
    ├── frontend.md
    ├── data.md
    └── training-models.md
```

**Structure Decision**: Monorepo tách `apps/web`, `services/inference-api` và `ai` để giao diện, dịch
vụ dự đoán và pipeline huấn luyện có trách nhiệm độc lập nhưng dùng chung contract và model metadata.
Raw video không nằm trong repository; `data/README.md` mô tả cách đặt dữ liệu cục bộ.

## Phase 0: Research Decisions

Các quyết định và phương án bị loại được ghi trong [research.md](research.md). Không còn
`NEEDS CLARIFICATION` kỹ thuật trước thiết kế.

## Phase 1: Design & Contracts

- [data-model.md](data-model.md) định nghĩa manifest dữ liệu, lớp ký hiệu, lần dự đoán và phiên bản model.
- [contracts/openapi.yaml](contracts/openapi.yaml) định nghĩa `GET /api/v1/health`,
  `GET /api/v1/model-info` và `POST /api/v1/predictions`, gồm request correlation header, timing breakdown,
  input-quality hints và stable error contract. Endpoint landmark JSON vẫn thuộc M2 và không nằm trong MVP.
- [quickstart.md](quickstart.md) định nghĩa các kịch bản kiểm chứng từ dữ liệu đến demo camera.

### Post-design Constitution Check

PASS. Thiết kế giữ dữ liệu video dự đoán ở ranh giới API, xóa trong `finally`, không thêm cơ sở dữ
liệu hoặc chức năng ngoài MVP, và tạo cổng đánh giá bắt buộc trước khi model được đánh dấu demo-ready.
Fixture/pilot chỉ mở khóa tích hợp, luôn bị đánh dấu không sẵn sàng cho demo chính thức và không làm
giảm ngưỡng chất lượng của full model.

## Complexity Tracking

Không có vi phạm hiến pháp hoặc độ phức tạp bổ sung cần theo dõi.
