# Kế hoạch ban đầu ViSign sau đối chiếu hiện trạng

Ngày chốt: 2026-11-07  
Nguồn sự thật: `specs/001-vsl-recognition-mvp/spec.md`, `plan.md`, `tasks.md`  
Nguyên tắc: code trên nhánh là bằng chứng tiến độ, không phải task hoàn thành trên `main`.

## 1. Mục tiêu gần nhất

Tạo một baseline chạy được trên `main` gồm camera frontend, FastAPI, shared MediaPipe/GRU pipeline và
fixture/pilot artifact qua cùng contract. Song song, hoàn thiện dữ liệu full 10 nghĩa và giữ công cụ
Admin/train-model như một track nội bộ có kiểm soát.

## 2. Những gì đã có

| Hạng mục | Hiện trạng | Cách tính trong kế hoạch |
|---|---|---|
| Backend | Nhánh `backend@b708c72`; báo cáo 14/16 yêu cầu backend đã làm, 119 tests đạt | `BRANCH`; còn T072–T073 và cần rerun sau merge |
| Frontend | Recognition UI, camera/error/result tests và browser tests đã có trên nhánh | `BRANCH`; còn T074–T075 và webcam thật |
| AI/model | Decoder, landmark schema v0.3, GRU, evaluation và artifact handoff code đã có | `PARTIAL`; pilot chạy được nhưng chưa đạt full gate |
| Data | Báo cáo có 42 clip phát triển, pilot Sốt-Chờ dùng 6 clip | `PARTIAL`; không thay thế full manifest 10 nghĩa |
| Admin | Inspect clip, pilot job, history và W&B UI/API đã có trên `admin/train-model` | Track nội bộ mới US4; cần contract/security/cleanup tests |

## 3. Bốn checkpoint

### CP1 - Baseline hợp nhất

- Tín: hoàn thành T072–T073, chuẩn hóa 404/405/307 và `Cache-Control: no-store`.
- Hiển: hoàn thành T074–T075, không auto-resubmit và dùng stable Vietnamese compatibility copy.
- Huy: review PR theo task ID; chạy lại backend/frontend/integration tests trên `main`.
- Kết quả: fixture camera→API→UI chạy trên `main`; chưa tuyên bố model quality.

### CP2 - Khóa pipeline và pilot evidence

- Cường: hợp nhất shared decoder/extractor/schema, parity, GRU và evaluation code.
- Quang: hoàn thành T076 cho pilot manifest, nguồn/quyền/hash/signer/split và coverage.
- Cường + Tín: chạy artifact handoff checker và pilot end-to-end.
- Kết quả: pilot được phép dùng smoke/integration, luôn `demoReady=false`.

### CP3 - Full 10 nghĩa

- Quang: hoàn thành T077 và T056; không leakage, đủ coverage meaning×signer.
- Cường: train/evaluate full; Macro-F1 ≥0.80, recall mỗi nghĩa ≥0.65, model card và latency.
- Tín + Hiển: đổi artifact không đổi contract; hiển thị đúng supported meanings/readiness.
- Kết quả: chỉ artifact full vượt mọi gate mới được đề xuất `demoReady=true`.

### CP4 - Nghiệm thu và demo

- Huy: quickstart, E2E webcam thật, fallback/rollback, demo rehearsal và usability test.
- Nhóm: đo p95 browser submit→result/error ≤3 giây trên laptop demo.
- Kết quả: verification report có commit/artifact/browser/camera version và mọi blocker đã đóng.

## 4. Track Admin/train-model (không chặn CP1)

- Tín: T078–T080 cho auth opt-in, contract, cleanup, sanitized errors và single-active-job.
- Hiển: T081–T082 cho typed client, component tests và route admin.
- Quang/Cường: cung cấp pilot handoff đã audit và chạy T083.
- Huy: T084 review secret, retention, public/private boundary và release claims.

Admin có thể merge sau khi test độc lập, nhưng không được mở public mặc định và không được thay full
release gate.

## 5. Quy tắc cập nhật nhiệm vụ

- Checkbox chỉ chuyển `[x]` khi implementation và bằng chứng đã nằm trên `main`.
- Mỗi PR ghi task ID, owner, reviewer, lệnh test và kết quả.
- Khi chỉ có code: trạng thái `BRANCH`; thiếu data/model/acceptance evidence: `PARTIAL`.
- Blocker quá 1 ngày được ghi vào file thành viên và `docs/team/implementation-status.md`.
- Không thêm chức năng sau MVP vào sprint nếu chưa có task ID, trigger và owner.

## 6. Quyết định thêm/bớt/cập nhật task

- T013 được thu nhỏ về vocabulary registry; bỏ việc gộp pilot và full manifest vào một checkbox.
- Thêm T076–T077 để tách pilot audit khỏi full 10-meaning manifest.
- T063 chuyển từ M1 candidate thành accessibility validation vì branch đã có test và frontend hiện
  coi đây là chức năng cần nghiệm thu.
- Giữ T072–T075 vì đây là gap HTTP đã đo được, chưa hoàn thành.
- Thêm T078–T084 cho US4 Admin/train-model; track này không làm tăng phạm vi public MVP.
