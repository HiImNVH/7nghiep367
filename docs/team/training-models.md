# P3 — Cường — AI implementation status

## Đã triển khai trong Model/Cường

| Task | Code và bằng chứng |
|---|---|
| T014–T016 | Decoder PyAV, extractor MediaPipe, transform/mask dùng chung, hash detector và schema. Có test corrupt clip, tọa độ chuẩn, missing shoulders/hands, WebM VP8/VP9 từ Chrome/Edge và tensor parity. Schema vẫn là draft chờ duyệt. |
| T017 | CLI trích manifest, chỉ nhận sample approved/verified, giữ nguyên label/split, ghi mã từ chối. Output mới được công bố nguyên thư mục sau khi hoàn tất. |
| T029, T033–T036 | GRU packed sequence, stable label order, loader, seed, cấu hình pilot/full, CLI train và validation checkpoint/threshold. Có test chạy train/evaluate tổng hợp và so trọng số giữa hai lần cùng seed. |
| T054, T057–T059 | Metric theo Meaning, split audit, full P0 gate, CLI evaluate và metadata writer. Evaluation giữ demoReady=false để chờ nghiệm thu. |
| T062 | docs/model-card.md công bố trạng thái, giới hạn và các giá trị còn chờ. |
| T065 | CLI benchmark local decode/extract/infer, p50/p95. Chưa có benchmark model VSL thật hoặc bằng chứng web end-to-end. |
| Phối hợp T037 | Adapter pilot/full dùng package AI chung, kiểm schema/extractor, nhận điểm GRU thật và ánh xạ lỗi. Fixture vẫn giữ contract hiện có. |

Đây là trạng thái triển khai code. Checkbox nghiệm thu thuộc tasks.md của lead và cần được đóng bằng bằng chứng tương ứng.

## Phạm vi kiểm tra

- Môi trường Python 3.12 riêng `.venv-ai`, cài editable AI và API.
- Test train/evaluate dùng hai lớp tổng hợp trong thư mục tạm, chỉ chứng minh cơ chế và tái lập trên cùng môi trường.
- Fixture browser được tạo bằng MediaRecorder Chrome/Edge từ canvas phát video tham chiếu cục bộ. Đây là bằng chứng codec/PTS trên trình duyệt, chưa phải E2E camera vật lý.
- Parity test dùng clip tham chiếu và checkpoint test tổng hợp để so tensor của đường offline với đường gọi predictor. Chưa có artifact VSL được duyệt.
- Clip HCM_Giấy_1.mp4 có 121 frame, đầu ra HAS_USABLE_FRAMES, tensor 32×234. Một lượt local ghi decode/extract/transform khoảng 11,8 giây. Đây là phép thử một clip, chưa phải p95 hoặc số liệu chất lượng model.
- Kiểm tra kiểu dữ liệu bằng cấu hình mypy cơ bản, chưa phải strict typing toàn dự án.

## Cần bàn giao hoặc review trước khi chạy thật

1. Quang bàn giao manifest pilot, class map và quyền sử dụng/nhãn đã duyệt. Sau đó bổ sung full catalog và split audit.
2. Cường, backend và Huy chốt schema, extractor/model bundle và dữ liệu thử. Không tự đổi schema draft sang approved chỉ để vượt kiểm tra.
3. Chạy train pilot, evaluation và negative/OOD bằng dữ liệu thật. Đo end-to-end trên laptop demo. Với thời gian preprocessing hiện đo được, cần tối ưu và đo lại trước khi tuyên bố đạt gate 3 giây.
4. Huy quyết định checkpoint và phát hành. Code hiện giữ fixture/pilot demoReady=false, evaluation chỉ báo model-quality eligibility cho full.

## Kết quả kiểm tra trước tối ưu runtime

- Toàn bộ pytest AI + backend + integration đạt 119 passed, 0 skipped trong 73,31 giây khi cấp các biến fixture browser và parity như mô tả trên. Có một cảnh báo deprecation từ thư viện TestClient/httpx.
- Ruff đạt cho ai/ và adapter GRU. Mypy cơ bản đạt cho 22 source files.
- Các test trích/train/evaluate dùng output tạm. Detector binaries, reference WebM, model test và tensor debug đều nằm trong đường dẫn bị Git bỏ qua.
- Chưa chạy lại browser UI sau thay đổi này. Các thay đổi nằm ở package AI và bridge backend, frontend không được sửa.

## Sau tối ưu runtime

Đã áp dụng draft schema v0.3, lấy mẫu PTS tối đa 64 frame, ba detector song song và CPU HighQoS theo tiến trình Windows. Benchmark 27 lượt tiền xử lý có p95 2506.14 ms, max 2514.28 ms. Số 11,8 giây ở phần trước là baseline v0.2 trước tối ưu. Xem [báo cáo đầy đủ](../performance-report.md). Gate end-to-end và chất lượng VSL vẫn chờ dữ liệu/model được duyệt.


Kiểm tra sau tối ưu đạt 152 test, 0 skipped; lint và mypy cơ bản đạt. Legacy serial/parallel đều trùng tensor và mask baseline. Báo cáo hiện tại không thay thế nghiệm thu model VSL và browser end-to-end.
