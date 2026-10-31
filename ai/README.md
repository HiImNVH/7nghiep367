# ViSign AI

Code cho P3 theo T014–T017, T029, T033–T036, T054, T057–T059, T062 và T065.
Chạy các lệnh bên dưới từ thư mục gốc `7nghiep367` trên nhánh `Model/Cường`.

## Môi trường và kiểm thử

Môi trường `.venv-ai` Python 3.12 đã được cài trên máy hiện tại. Máy mới cần Python 3.12, tạo môi trường và cài hai package.

```powershell
py -3.12 -m venv .venv-ai
.\.venv-ai\Scripts\python -m pip install -e "./ai[dev]" -e "./services/inference-api[dev]"
.\.venv-ai\Scripts\python ai/setup_models.py
```

Các detector tải từ Google được kiểm tra SHA-256 theo `configs/download-manifest.json`.
Detector phục vụ trích điểm. Trọng số GRU sẽ được tạo bởi lệnh train.

```powershell
New-Item -ItemType Directory -Force .local | Out-Null
.\.venv-ai\Scripts\python -m pytest --basetemp .local/test-run-01
.\.venv-ai\Scripts\python -m ruff check ai services/inference-api/src/visign_api/inference/gru_predictor.py
.\.venv-ai\Scripts\python -m mypy ai/src
```

Dùng tên `test-run-*` mới cho lần kiểm tra khác. Test train/evaluate dùng dữ liệu tổng hợp trong thư mục tạm để kiểm tra cơ chế. Kết quả đó không được dùng làm báo cáo chất lượng VSL.

Các test clip WebM thật được mở bằng `VISIGN_CHROME_WEBM`, `VISIGN_EDGE_WEBM`. Test parity offline/serving dùng `VISIGN_PARITY_CLIP`, `VISIGN_PARITY_ARTIFACT`. Thiếu đầu vào thì test ghi `SKIPPED`, cần bổ sung bằng chứng trước khi đóng M0.

## Kiểm tra một clip

```powershell
.\.venv-ai\Scripts\python -m visign_ai.landmarks.inspect_clip --clip "K:/Dự án ViSign/Data/1. Giấy tờ (giấy)/HCM_Giấy_1.mp4" --output .local/inspect-01
```

Lệnh debug offline xuất tensor, tọa độ gốc, mask và report. API gọi trực tiếp `visign_ai.landmarks.pipeline.process_video` và không xuất các file debug.

Schema hiện giữ `DRAFT_PENDING_LEAD_REVIEW`. Nó mô tả bản thử 78 điểm, 32 bước, 234 đặc trưng. Lệnh train và adapter API yêu cầu schema `APPROVED` do nhóm đã chốt. Việc đổi trạng thái cần đi cùng review phiên bản, thứ tự điểm, chuẩn hóa và bundle detector.

## Nhận dữ liệu và trích xuất

Quang bàn giao manifest CSV có `sampleId`, `classLabel`, `recordingSessionId`, `signerId`, `sourceUri`, `rawPath`, `licenseStatus`, `verificationStatus`, `split`. `rawPath` phải tương đối với kho dữ liệu. Chỉ nhận `approved` và `verified`, giữ nguyên nhãn/split bàn giao. Full yêu cầu signer đầy đủ, không trùng giữa các tập. Pilot thiếu signer sẽ được ghi `session-only`.

Class map JSON do nhóm chốt ánh xạ từng class label sang `meaningId` và `displayText`. Các biến thể của cùng nghĩa phải có cùng nội dung hiển thị. `--classes` chọn tập lớp theo đúng thứ tự sẽ lưu vào model.

Sau khi có các file được duyệt, thay đường dẫn trong các lệnh mẫu theo bàn giao thực tế.

```powershell
.\.venv-ai\Scripts\python -m visign_ai.landmarks.extract_manifest --manifest data/manifests/pilot.csv --raw-root "K:/Dự án ViSign/Data" --schema ai/configs/feature_schema.json --output ai/processed/pilot-v1
```

Đầu ra có `manifest.csv`, NPZ và `extraction-report.json`. Mẫu lỗi được ghi bằng sample ID/mã lỗi. Nếu có mẫu bị loại, bàn giao lại coverage cho Quang/Huy review trước khi train. Mỗi output phải là đường dẫn mới. Chỉ công bố thư mục khi lệnh hoàn tất.

## Train, evaluate và benchmark

```powershell
.\.venv-ai\Scripts\python -m visign_ai.training.train --manifest ai/processed/pilot-v1/manifest.csv --feature-root ai/processed/pilot-v1 --class-map data/manifests/classes.json --schema ai/configs/feature_schema.json --config ai/configs/pilot-gru.yaml --kind pilot --model-version pilot-v1 --output ai/artifacts/pilot-v1
.\.venv-ai\Scripts\python -m visign_ai.evaluation.evaluate --artifact ai/artifacts/pilot-v1 --manifest ai/processed/pilot-v1/manifest.csv --feature-root ai/processed/pilot-v1 --output ai/artifacts/pilot-v1-evaluated
.\.venv-ai\Scripts\python -m visign_ai.evaluation.benchmark_inference --artifact ai/artifacts/pilot-v1-evaluated --clips "PATH_TO_REVIEWED_CLIP.webm" --repeats 5 --output .local/benchmark-01
```

Train mặc định CPU. `--device cuda` cho GPU nếu cài PyTorch CUDA phù hợp. Seed, cấu hình và lịch sử validation được lưu. Chọn checkpoint và threshold chỉ dùng validation. Evaluation dùng test từ đúng manifest đã hash khi train, gom metric theo Meaning và lưu confusion matrix.

Full dùng `--kind full`, cấu hình `ai/configs/p0-gru.yaml` và bắt buộc `--p0-meanings data/manifests/p0-meanings.csv`. Catalog phải chứa đúng 10 `meaningId` đã đóng băng. Pilot chỉ nhận tối đa 3 nghĩa.

Evaluation xuất `modelQualityGatePassed` khi full đúng catalog, signer-held-out, Macro-F1 ≥ 0.80 và recall mỗi nghĩa ≥ 0.65. Nó giữ `demoReady=false` để chờ kiểm tra toàn hệ thống và Huy duyệt. Báo cáo negative/OOD cần bộ clip được review riêng. Benchmark ở đây đo decode/extract/GRU, phần HTTP và hiển thị trên web cần đo trong tổng duyệt.

## Nối vào API

Fixture mặc định tiếp tục dùng được với môi trường backend cũ. Với artifact pilot/full hợp lệ, chạy API bằng `.venv-ai` và cấu hình cả phiên bản schema.

```powershell
$env:MODEL_ARTIFACT_PATH = (Resolve-Path ai/artifacts/pilot-v1-evaluated).Path
$env:FEATURE_SCHEMA_VERSION = (Get-Content ai/artifacts/pilot-v1-evaluated/model_info.json -Raw | ConvertFrom-Json).featureSchemaVersion
.\.venv-ai\Scripts\python -m uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
```

Thiếu detector, trọng số, sai version/schema hoặc thiếu schema approval sẽ không tải được artifact. Registry giữ artifact hoạt động trước đó theo cơ chế rollback hiện có. Thay artifact cần restart API và thử lại health/model-info/prediction. Dừng uvicorn bằng Ctrl+C.

## Fixture codec tự tạo

Khi frontend đã cài dependencies, lệnh sau ghi bốn WebM Chrome/Edge VP8/VP9 từ một video tham chiếu. Video sinh ra nằm ngoài Git.

~~~powershell
node ai/tests/record_browser_fixtures.mjs "PATH_TO_REFERENCE.mp4" .local/browser-fixtures
$env:VISIGN_BROWSER_FIXTURES = (Resolve-Path .local/browser-fixtures).Path
~~~

Fixture dùng canvas capture, kiểm tra codec và PTS. Kiểm tra camera vật lý và benchmark toàn luồng vẫn cần thực hiện trong tổng duyệt.

Kết quả tối ưu tiền xử lý và giới hạn bằng chứng được ghi tại [performance-report.md](../docs/performance-report.md).


## Chạy lại benchmark tiền xử lý

~~~powershell
.\.venv-ai\Scripts\python -m visign_ai.evaluation.benchmark_preprocessing --clips "K:/Dự án ViSign/Data/1. Giấy tờ (giấy)/HCM_Giấy_1.mp4" --repeats 5 --output .local/preprocessing-recheck-01
~~~

Windows mặc định bật chế độ hiệu năng cho riêng tiến trình AI. Để giữ chính sách CPU mặc định, đặt `$env:VISIGN_CPU_PERFORMANCE_MODE='0'` trước khi khởi động tiến trình. Restart tiến trình khi đổi cấu hình này. Nếu Windows không hỗ trợ, report ghi applied=false và inference vẫn hoạt động.

Schema v0.3 lấy tối đa 64 frame theo PTS rồi tạo chuỗi 32 bước. Bản v0.2 đã lưu trong `configs/feature_schema.legacy-v0.2.json` và artifact cũ vẫn dùng schema đi kèm. Dữ liệu/model mới phải được trích/train theo đúng schema được nhóm duyệt.
