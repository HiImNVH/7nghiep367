<!--
Sync Impact Report
- Version change: template -> 1.0.0
- Added principles:
  - I. An toan va trung thuc voi nguoi dung
  - II. Du lieu co nguon goc va bien the ro rang
  - III. Chat luong mo hinh phai do duoc
  - IV. Quyen rieng tu theo mac dinh
  - V. MVP don gian, chay xuyen suot
- Added sections:
  - Rang buoc san pham va du lieu
  - Quy trinh phat trien va cong chat luong
- Removed sections: none
- Follow-up TODOs: none
-->
# ViSign Constitution

## Core Principles

### I. An toàn và trung thực với người dùng
ViSign MUST được mô tả là công cụ hỗ trợ thử nghiệm, không phải phiên dịch viên chuyên nghiệp.
Mọi kết quả nhận diện MUST hiển thị độ tin cậy hoặc trạng thái không chắc chắn, và hệ thống MUST
có kết quả “Không nhận diện được” thay vì buộc chọn một từ. Giao diện MUST cảnh báo rằng kết quả
có thể không chính xác và không được dùng thay thế hỗ trợ chuyên môn trong tình huống y tế, pháp
lý hoặc khẩn cấp. Nguyên tắc này bảo vệ người dùng khỏi việc tin quá mức vào dự đoán của mô hình.

### II. Dữ liệu có nguồn gốc và biến thể rõ ràng
Mỗi mẫu dữ liệu MUST lưu được ý nghĩa, nhãn lớp, vùng miền, nguồn, điều kiện sử dụng và trạng thái
xác minh. Các động tác thực sự khác nhau cho cùng một ý nghĩa MUST là các lớp riêng; khác biệt về
người thực hiện, tốc độ, góc quay hoặc tay thuận không tự động tạo lớp mới. Dữ liệu không phải Ngôn
ngữ Ký hiệu Việt Nam, sai nhãn hoặc không rõ quyền sử dụng MUST bị loại khỏi tập huấn luyện được
phê duyệt. Nguyên tắc này làm cho kết quả có thể kiểm tra và tránh trộn lẫn dữ liệu không tương thích.

### III. Chất lượng mô hình phải đo được
Mỗi phiên bản mô hình được chấp nhận MUST gắn với phiên bản dữ liệu, cách chia tập và báo cáo đánh
giá. Tập kiểm thử MUST tách theo người thực hiện hoặc phiên quay để tránh rò rỉ dữ liệu. Báo cáo
MUST có ít nhất độ chính xác, precision, recall, confusion matrix, độ trễ nhận diện và kết quả với
người chưa xuất hiện trong tập huấn luyện. Các ngưỡng nghiệm thu MUST được ghi trong đặc tả của
từng mốc phát hành. Nguyên tắc này ngăn việc đánh giá sản phẩm chỉ bằng một vài lần demo thuận lợi.

### IV. Quyền riêng tư theo mặc định
Video camera, landmark và thông tin có thể nhận dạng cá nhân MUST chỉ được thu thập cho mục đích
đã công bố. ViSign MUST không lưu video người dùng sau khi dự đoán nếu chưa có sự đồng ý rõ ràng.
Dữ liệu dùng để huấn luyện MUST có quyền sử dụng phù hợp; thông tin nhạy cảm MUST không xuất hiện
trong log, lỗi hoặc kho mã nguồn công khai. Nguyên tắc này đặc biệt quan trọng vì sản phẩm xử lý
hình ảnh khuôn mặt, bàn tay và cơ thể.

### V. MVP đơn giản, chạy xuyên suốt
Mỗi mốc MUST ưu tiên một luồng hoàn chỉnh từ camera hoặc video đến kết quả tiếng Việt, trạng thái
không chắc chắn, kiểm thử và bằng chứng đánh giá. Nhóm MUST hoàn thành phạm vi P0 trước khi mở rộng
từ vựng hoặc thêm tính năng P1/P2. Kiến trúc và công cụ MUST tuân theo KISS và YAGNI; đăng nhập,
lịch sử, hội thoại liên tục, chuyển văn bản thành giọng nói và hạ tầng phức tạp chỉ được thêm khi có
đặc tả được phê duyệt. Nguyên tắc này giữ cho bản demo có thể hoàn thành và kiểm chứng trong thời gian
hackathon.

## Ràng buộc sản phẩm và dữ liệu

- Đầu ra dành cho người dùng MUST là tiếng Việt; mã lớp và vùng miền chỉ là metadata nội bộ.
- ViSign MUST ưu tiên biến thể TP.HCM nhưng MAY hỗ trợ biến thể vùng khác khi có nguồn phù hợp.
- Một ý nghĩa MAY ánh xạ từ nhiều lớp ký hiệu, nhưng các lớp đó MUST hiển thị cùng một nội dung.
- Mẫu chưa được người có chuyên môn xác minh MUST được đánh dấu `verified: false`.
- Repository công khai MUST không chứa video có bản quyền, giấy phép hoặc sự đồng ý không rõ ràng.
- Phạm vi P0, P1 và P2 MUST được ghi rõ trong từng đặc tả; thay đổi phạm vi cần được chấp thuận trước
  khi triển khai.

## Quy trình phát triển và cổng chất lượng

- Mỗi tính năng MUST đi qua đặc tả, làm rõ, kế hoạch và danh sách task trước khi triển khai.
- Mỗi yêu cầu MUST có tiêu chí nghiệm thu kiểm thử được theo Given/When/Then, bao gồm trường hợp
  thành công, đầu vào không hợp lệ và trường hợp biên.
- Thay đổi giao diện, API, pipeline dữ liệu hoặc mô hình MUST có kiểm thử phù hợp và bằng chứng chạy.
- Mọi hợp đồng giữa frontend, backend và mô hình MUST được ghi rõ, có phiên bản và được kiểm thử tích hợp.
- Thay đổi ngoài phạm vi, refactor và tăng phiên bản MUST được người dùng phê duyệt trước.
- Không được commit, amend hoặc force-push nếu người dùng chưa yêu cầu rõ ràng.

## Governance

Hiến pháp này áp dụng cùng `.agent/core.md`; khi có xung đột, quy tắc dự án cụ thể trong hiến pháp
này được xem là T2 và có ưu tiên cao hơn đối với ViSign. Mọi đặc tả, kế hoạch, task và review MUST
kiểm tra tuân thủ các nguyên tắc trên. Sửa đổi hiến pháp MUST ghi lý do, ảnh hưởng, kế hoạch chuyển
đổi nếu có và cập nhật phiên bản theo semantic versioning: MAJOR cho thay đổi không tương thích,
MINOR cho nguyên tắc hoặc hướng dẫn mới, PATCH cho làm rõ không đổi ý nghĩa. Mọi ngoại lệ MUST được
ghi trong kế hoạch của tính năng và được người dùng phê duyệt.

**Version**: 1.0.0 | **Ratified**: 2026-10-19 | **Last Amended**: 2026-10-19
