# ViSign GRU model card — pending real training

## Trạng thái

Chưa có artifact GRU được train trên manifest VSL đã duyệt. Bản hiện tại bổ sung code, test và công cụ đánh giá. API mặc định vẫn dùng fixture. `demoReady=false`.

## Kiến trúc đã triển khai

PyAV → lấy mẫu toàn clip theo PTS, tối đa 64 frame → MediaPipe hai tay, pose và tập con mặt → tọa độ chuẩn hóa theo vai, resampling theo PTS và mask từng điểm → GRU packed sequence → class label → Meaning tiếng Việt. Cùng package được dùng cho extraction offline và predictor API.

Schema thử `visign-xy-32-v0.3-draft` đang chờ lead review. Cấu hình pilot có hidden size 64, full có hidden size 128. Các cấu hình này là baseline để thử, chưa có số liệu xác nhận hiệu quả. GRU trả thứ tự lớp từ artifact, threshold được chọn trên validation.

## Bằng chứng còn chờ

| Nội dung | Trạng thái |
|---|---|
| Manifest/version, nguồn và quyền sử dụng | Chờ Quang bàn giao |
| Supported meanings và class map thật | Chờ catalog/pilot subset duyệt |
| Sample/signer counts và signer-held-out provenance | Chờ manifest/split |
| Accuracy, precision/recall từng nghĩa, Macro-F1, confusion matrix | Chờ train/evaluate thật |
| Negative/OOD và rule từ chối | Có công cụ threshold validation, chờ dữ liệu đánh giá |
| p50/p95 decode/extract/infer trên laptop demo | Có CLI, chờ artifact/clip đánh giá |
| 95% kết quả/lỗi trong ≤3 giây qua web/API | Chờ tổng duyệt toàn luồng |
| WebM Chrome/Edge và train/API parity thực tế | Có test opt-in, cần cung cấp clip/artifact |
| Phê duyệt demo | Huy quyết định sau đủ gate |

## Giới hạn và cảnh báo

MVP xử lý một ký hiệu riêng lẻ. Tọa độ vai không đủ tin cậy hoặc không có tay hữu dụng dẫn đến từ chối. Nhãn trái/phải của MediaPipe và ảnh camera phản chiếu cần kiểm tra khi duyệt schema. Pipeline khởi tạo detector mỗi clip, vì vậy thời gian khởi tạo nằm trong benchmark. Hiện chưa có bằng chứng độ chính xác hoặc đạt giới hạn thời gian của sản phẩm.

ViSign là sản phẩm thử nghiệm. Kết quả có thể không chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.


Kết quả tối ưu tiền xử lý và giới hạn bằng chứng được ghi tại [performance-report.md](performance-report.md).
