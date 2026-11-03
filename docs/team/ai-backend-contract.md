# Hợp đồng kỹ thuật giữa AI và backend

Ngày review code: 01/11/2026. Nhánh áp dụng: `Model/Cường`, repo `7nghiep367`.
Theo xác nhận của Cường trong cuộc trao đổi ngày 01/11/2026, Tín đã đồng ý năm điểm tích hợp: video WebM/giới hạn đầu vào, pipeline/schema/extractor chung, artifact qua MODEL_ARTIFACT_PATH, confidence/lỗi và kiểm tra parity/nạp model/cleanup. Đây là xác nhận phương án tích hợp; phần review clip đại diện trước duyệt schema vẫn giữ nguyên. Không suy ra Huy đã nghiệm thu hoặc dữ liệu đã được duyệt.

## Phạm vi đã cố định trong code

| Nội dung | Quy định |
|---|---|
| API | POST `/api/v1/predictions`, multipart field `clip`; GET `/api/v1/health`, GET `/api/v1/model-info` |
| Video qua HTTP | WebM VP8/VP9, tối đa 10 MiB (10,485,760 bytes); đầu vào MP4 được dùng ở công cụ offline, không mở thêm upload MP4 |
| Thời lượng | Từ 300 đến 6000 ms, đo từ PTS giải mã, không tin số client gửi. Frontend mặc định dừng ghi ở 5000 ms |
| Camera | MediaRecorder ghi stream gốc. CSS phản chiếu preview không lật dữ liệu gửi API; pipeline không tự flip video |
| Schema hiện tại | `visign-xy-32-v0.3-draft`; 21 điểm tay trái, 21 tay phải, pose 11–16, 30 điểm mặt theo đúng thứ tự trong JSON |
| Tensor | float32 `[32,234]`: 156 giá trị XY rồi 78 validity flags; điểm thiếu đặt XY=0, validity=0; các mask NPZ được ghi rõ trong schema |
| Chuẩn hóa | Tâm hai vai 11,12; chia khoảng cách vai trong tọa độ pixel có tính tỉ lệ khung hình. Không suy diễn tọa độ tay mất |
| Lấy mẫu | Tối đa 64 frame theo PTS trải toàn clip, sau đó nội suy 32 bước. Chỉ nội suy khi điểm ở cả hai mẫu lân cận đều hợp lệ |
| Extractor | MediaPipe 1.1.1, `tasks-hand-pose-face-1.1.1-24d9ff64192c8dc3`; detector hash tại `ai/configs/download-manifest.json`; ba nhóm chạy song song, mỗi clip reset tracking |
| Đường dùng chung | Train trích đặc trưng và GRU API cùng gọi `visign_ai.landmarks.pipeline.process_video`, dùng schema đi kèm artifact |
| Quyết định | GRU trả class/confidence; API so với acceptanceThreshold từ validation. Không đạt: accepted=false, classLabel=null, text='Không nhận diện được' |
| Readiness | Fixture/pilot luôn demoReady=false. Full còn cần gate dữ liệu, chất lượng, toàn luồng và Huy nghiệm thu |

## Gói Cường giao cho backend

Giao nguyên thư mục output bất biến, gồm `model.pt`, `feature_schema.json`, `model_info.json`, `training-report.json`; bản evaluated bổ sung `evaluation-report.json` và confusion matrix. Không đổi thứ tự classLabels hoặc meaningMap bằng tay sau train.

Checkpoint mới ràng buộc cả nội dung schema và `classLabels`, `meaningMap`, `displayTextMap`. Đổi thứ tự output hoặc chữ hiển thị sẽ bị từ chối khi nạp. Checkpoint cũ còn được giữ tương thích bởi loader; lệnh kiểm tra bàn giao mới từ chối checkpoint thiếu label binding, yêu cầu train lại bằng code mới. Không tự thêm binding cho trọng số cũ để tuyên bố đã kiểm chứng.

Detector là tài nguyên riêng, không phải model nhận diện. Máy backend cài cả package `ai` và `services/inference-api` bằng Python 3.12, chạy `ai/setup_models.py` để tải đủ detector; có thể chọn thư mục detector qua `VISIGN_MODEL_DIR`.

## Kiểm tra trước khi nạp

Chạy tại gốc repo, sau khi nhận artifact thật. Thay đường dẫn bằng thư mục bàn giao thực tế:

```powershell
$env:MODEL_ARTIFACT_PATH = (Resolve-Path 'ai/artifacts/pilot-v1-evaluated').Path
$env:FEATURE_SCHEMA_VERSION = (Get-Content "$env:MODEL_ARTIFACT_PATH/model_info.json" -Raw | ConvertFrom-Json).featureSchemaVersion
.\.venv-ai\Scripts\python -m visign_api.inference.check_artifact --artifact "$env:MODEL_ARTIFACT_PATH" --clip 'PATH_TO_REVIEWED_CLIP.webm'
```

Lệnh dùng registry mới, không mượn model trước đó khi candidate bị lỗi; exit code 1 nghĩa là chưa được nạp. Mặc định kiểm schema APPROVED, schema/checkpoint binding, detector, thứ tự lớp/nghĩa và loại artifact. Có `--clip` thì kiểm WebM/size, so tensor offline và đường GRU của adapter (atol=1e-6), cả mask điểm/nhóm/mask tensor, rồi gọi GRU qua adapter. Không có clip thì report ghi parity NOT_RUN, chưa đủ bằng chứng parity.

Sau khi kiểm tra đạt, khởi động API trong cùng terminal có các biến môi trường trên:

```powershell
.\.venv-ai\Scripts\python -m uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
```

Kiểm tra health/model-info để chắc đang chạy artifactKind pilot/full đúng modelVersion; fixture trả cố định để thử giao tiếp. Đổi MODEL_ARTIFACT_PATH cần restart tiến trình. Registry giữ model đang hoạt động nếu reload candidate lỗi trong cùng tiến trình; đây không phải rollback lưu qua restart. Khi restart mà artifact lỗi, service degraded và không được suy luận bằng fixture thay thế. Muốn quay lại bản trước: đặt đường dẫn/version bản trước rồi restart và kiểm tra health.

## Lỗi và kiểm thử tích hợp

Giữ contract hiện có: INVALID_REQUEST, UNSUPPORTED_MEDIA_TYPE, CLIP_TOO_LARGE, CLIP_TOO_SHORT, CLIP_TOO_LONG, NO_PERSON_DETECTED, INSUFFICIENT_LANDMARKS, CLIP_DECODE_FAILED, SERVICE_BUSY, MODEL_NOT_READY, PREDICTION_FAILED. INVALID_REQUEST của pipeline giữ mã 400; lỗi giải mã/schema bất ngờ đi theo lỗi decode của adapter hiện tại. Không trả landmark/frame thô trong response hoặc log HTTP. File clip tạm được cleanup trên cả success và error theo cơ chế backend.

Backend đang giới hạn một lượt inference đồng thời; giá trị 3 giây của coordinator là thời gian đợi slot, không bảo đảm thời gian trả kết quả toàn luồng. Gate p95 ≤3 giây vẫn phải đo trên web với model thật.

## Phần còn chờ để mở pilot

Hợp đồng kỹ thuật đã được mô tả và kiểm tra bằng code. Schema vẫn giữ DRAFT_PENDING_LEAD_REVIEW: chưa tự đổi APPROVED, vì chưa có review độ giữ được diễn biến ký hiệu sau lấy mẫu, quy ước trái/phải với clip camera đại diện và dữ liệu pilot được duyệt. Khi review hoàn tất, cập nhật trạng thái có căn cứ; nếu thay đổi quy tắc tensor thì tạo version mới, trích lại và train lại. Không đổi schema của artifact đã phát hành.

Quang bàn giao pilot.csv, class map, video approved/verified và split audit. Cường train/evaluate thật rồi giao artifact; Tín chạy preflight và HTTP, Hiển thử camera/result/error/retry; Huy quyết định checkpoint/full và phát hành. Kiểm thử với GRU tổng hợp chỉ chứng minh cơ chế, không chứng minh nhận diện VSL.

## Bằng chứng review ngày 01/11/2026

160 test AI/backend/integration passed, 0 skipped trong 35,12 giây. Có một cảnh báo deprecation của Starlette TestClient/httpx. Ruff đạt; mypy cơ bản đạt trên 25 source files.

Lệnh check_artifact chạy thật với artifact tổng hợp vừa train bởi CLI test và Chrome VP8 WebM: load thành công, label binding hợp lệ, tensor [32,234], maxAbsDiff=0 và mask điểm/nhóm/tensor khớp hoàn toàn. Artifact tổng hợp giữ demoReady=false. Báo cáo máy đọc được ở [ai-backend-handoff.json](../verification/ai-backend-handoff.json).

Bằng chứng này xác nhận hợp đồng kỹ thuật trên môi trường hiện tại. Chưa phải chấp thuận cá nhân của Tín/Huy, chưa chứng minh độ chính xác trên dữ liệu VSL hoặc thời gian hiển thị kết quả qua camera vật lý.


## Sau khi Tín đồng ý phương án tích hợp

Code thêm scripts/Export-Model.ps1 để xuất artifact evaluated vào thư mục mới, kiểm tensor/mask bằng golden WebM và tạo FILES-SHA256.json. Gói xuất có sáu file model/schema/metadata/train/evaluation/confusion matrix, parity-report.json và checksum. Không sửa input artifact. Metadata evaluation phải khớp dataset/metric/ngày với model_info. Toàn gói chỉ công bố nếu mọi kiểm tra thành công.

Registry kiểm checksum khi có manifest, trước khi đọc trọng số; lỗi candidate giữ nguyên predictor đang hoạt động theo cơ chế cũ. Start-Api.ps1 yêu cầu manifest đối với pilot/full và chạy preflight trước khi mở API. Dùng -UseFixture tường minh để chạy fixture. Checksum là kiểm tra toàn vẹn vận chuyển, không phải chữ ký phê duyệt.

scripts/Measure-AI.ps1 chạy MediaPipe thật mà chưa cần trọng số GRU để hai máy lấy range tiền xử lý. Báo cáo có min/p50/p95/max, phiên bản runtime và schema. Không dùng số đo này thay gate web/GRU. Xem hướng dẫn tại ai/README.md.


Lượt kiểm tra sau triển khai: 175 test đạt; script export/start/HTTP/cleanup và parity với GRU tổng hợp đạt. Range MediaPipe trên máy Cường 5 lượt: 1,844–2,149 giây, p95 2,105 giây; chưa có số đo máy Tín, model VSL thật hoặc gate hiển thị toàn luồng. Bằng chứng tại [tin-integration-next-step.json](../verification/tin-integration-next-step.json).
