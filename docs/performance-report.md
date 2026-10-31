# Kiểm tra tối ưu AI trên laptop demo

## Phạm vi

Đo local trên Intel Core i7-12700H, Windows 11, Python 3.12, MediaPipe 1.1.1, PyAV 19.0.2. Các số dưới đây là phép đo code thực tế trên bộ clip tham chiếu nhỏ. Bộ clip này chưa phải tập test chất lượng do Quang/Huy duyệt.

Tiền xử lý được đo bằng wall clock, gồm đọc/kiểm hash detector, decode, lấy mẫu, tạo detector, trích điểm, đóng detector và tạo tensor. Thời gian import Python/package trước khi gọi hàm nằm ngoài phép đo. Với API, import và load model diễn ra lúc service khởi động.

## Thay đổi đã áp dụng

1. Lấy tối đa 64 frame theo PTS trên toàn clip, giữ frame đầu/cuối. Clip có ít hơn 64 frame giữ toàn bộ frame. Chuỗi cuối vẫn 32 bước × 234 đặc trưng.
2. Ba detector hand/pose/face chạy trong ba worker độc lập. Mỗi detector nhận timestamp tăng dần và tracking state mới cho mỗi clip. Các worker hoàn tất trước khi detector đóng, kể cả khi có lỗi.
3. Trên Windows, tiến trình AI mặc định yêu cầu HighQoS cho execution speed. Biến `VISIGN_CPU_PERFORMANCE_MODE=0` trước khi khởi động giữ chính sách mặc định. Thao tác chỉ áp dụng tiến trình hiện tại, giữ nguyên power plan của máy. Trạng thái áp dụng có trong report. Thử nghiệm đã phát hiện các lần gọi sau chậm rõ khi để hệ điều hành tự chọn QoS.
4. Clip sai độ dài bị từ chối sau decode và trước khi chạy detector, giữ mã lỗi API.
5. Schema mới mang phiên bản `visign-xy-32-v0.3-draft`, vẫn chờ lead duyệt. Artifact lưu schema riêng. Checkpoint mới ràng buộc hash nội dung schema. Schema cũ giữ cách lấy mọi frame, và checkpoint legacy chỉ được nạp khi khớp chính xác schema legacy.

Tài liệu Windows cho cơ chế QoS nằm tại [SetProcessInformation của Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-setprocessinformation).

## Kết quả tiền xử lý

- Baseline HCM_Giấy_1.mp4 có 121 frame, một lượt wall clock 11103.44 ms.
- Cùng clip sau tối ưu có p50 2004.04 ms, p95 2105.34 ms qua ba lượt.
- Toàn bộ 9 clip × 3 lượt có p50 1204.46 ms, p95 2506.14 ms, cao nhất 2514.28 ms.
- 27/27 lượt tiền xử lý dưới 3 giây. Tensor của mỗi clip lặp lại có sai khác lớn nhất 0.0.
- Thử song song mà vẫn lấy tất cả frame cho tensor/mask trùng baseline, sai khác tensor lớn nhất 0.0, mask equal=True.
- Lấy mẫu trước trích điểm có thể đổi kết quả tracking so với v0.2, nên đã tăng phiên bản schema. Trên clip Giấy, tỷ lệ tensor có vai + ít nhất một tay hữu dụng ở baseline và mức 64 frame đều là 0.40625. Chỉ số này không thay thế accuracy/recall của model.

| Clip | Decode → trích frame | p50 ms | p95 ms |
|---|---|---|---|
| HCM_Giấy_1.mp4 | 121 → 64 | 2004.04 | 2105.34 |
| O_Đau bụng_1.mp4 | 137 → 64 | 2510.46 | 2513.90 |
| O_Thuốc_1.mp4 | 161 → 64 | 2383.72 | 2484.82 |
| O_Xin chào_1.mp4 | 116 → 64 | 1866.60 | 1971.13 |
| O_Cảm ơn_1.mp4 | 39 → 39 | 1129.43 | 1196.96 |
| chrome-vp8.webm | 16 → 16 | 640.32 | 680.81 |
| chrome-vp9.webm | 37 → 37 | 1122.21 | 1163.56 |
| msedge-vp8.webm | 37 → 37 | 1124.38 | 1134.51 |
| msedge-vp9.webm | 37 → 37 | 1186.50 | 1421.63 |

Chrome/Edge fixture được tạo bằng MediaRecorder từ canvas phát video tham chiếu. Chưa thay thế kiểm thử camera vật lý trên browser.

## Kiểm tra API

5 request TestClient dùng WebM thật và checkpoint GRU tổng hợp có p95 **1356.40 ms**. Qua đường này, tensor offline/API trùng trong atol 1e-6, response giữ contract và clip tạm được xóa sau mỗi request. Checkpoint tổng hợp dùng để kiểm tra cơ chế, không phải model VSL đã train. Phép đo loại trừ network và cập nhật giao diện trên browser.

## Đối chiếu kế hoạch lead

- Giữ PyAV, MediaPipe hai tay/pose/mặt, PyTorch GRU và cùng package `visign_ai.landmarks` cho train/API.
- Chuẩn hóa theo vai, mask điểm thiếu và resampling vẫn dùng chung. Không điền giả landmark bị thiếu.
- Sampling policy và execution policy có trong schema. Schema mới chưa được tự duyệt.
- Không đổi OpenAPI, threshold acceptance, split hoặc nhãn bàn giao. Không thêm ONNX/model mới hay mở scope M1/M2.
- Fixture/pilot vẫn demoReady=false. Chưa train trên dữ liệu chưa duyệt.
- Gate chính thức vẫn cần model full 10 nghĩa, signer-held-out, Macro-F1 ≥0.80, recall mỗi nghĩa ≥0.65 và 95% kết quả/lỗi hiển thị trong ≤3 giây trên môi trường demo.

Số đo hiện tại tạo headroom cho GRU/API, chưa chứng minh gate end-to-end với model VSL thật. Cần train/evaluate lại theo schema được duyệt, đo negative/OOD, benchmark trên dữ liệu được review và tổng duyệt browser.

## Bằng chứng

- [27 lượt tiền xử lý](verification/ai-preprocessing-benchmark.json)
- [5 request API với GRU tổng hợp](verification/ai-synthetic-api-benchmark.json)


## Kiểm tra cuối sau tối ưu

- 152 test AI + backend + integration đạt, 0 skipped, trong 46,44 giây khi cấp đủ fixture đã mô tả. Có một cảnh báo deprecation từ TestClient/httpx.
- Ruff đạt. Mypy cơ bản đạt cho 25 source files.
- Test bao gồm PTS bất thường, frame thiếu, lỗi decoder/detector, dọn tài nguyên của worker, reset tracking từng clip, hash schema/checkpoint, legacy compatibility, threshold/contract, clip cleanup và parity offline/API.
- Đã so lại code hiện tại với baseline ở cả legacy serial và legacy parallel all-frame. Tensor max abs diff = 0.0, mask giống nhau trong cả hai chế độ.
- [Bằng chứng legacy parity](verification/ai-legacy-parity.json).

Chạy lại phép đo preprocessing bằng `python -m visign_ai.evaluation.benchmark_preprocessing`. Xem lệnh đầy đủ trong ai/README.md. Giữ toàn bộ video, detector binaries và model kiểm thử ngoài Git.
