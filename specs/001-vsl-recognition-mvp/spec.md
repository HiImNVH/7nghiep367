# Feature Specification: ViSign VSL Recognition MVP

**Feature Branch**: `001-vsl-recognition-mvp`

**Created**: 2026-10-19

**Status**: Ready for planning

**Input**: User description: "Xây dựng ViSign, một ứng dụng web thử nghiệm nhận diện Ngôn ngữ Ký hiệu Việt Nam và chuyển từng ký hiệu riêng lẻ thành chữ tiếng Việt, ưu tiên biến thể TP.HCM, có độ tin cậy và trạng thái không nhận diện được."

## Clarifications

### Session 2026-10-19

- Q: Bản MVP đầu tiên phải nhận diện ổn định bao nhiêu ý nghĩa tiếng Việt? → A: 10 từ P0; 20 từ còn lại mở rộng sau. Danh sách 10 từ được chốt sau khi thành viên phụ trách hoàn tất lọc và bổ sung raw material.
- Q: MVP đầu tiên phải nhận ký hiệu từ nguồn đầu vào nào? → A: Video được dùng cho huấn luyện và đánh giá; sản phẩm nhận hình ảnh trực tiếp từ camera để kiểm tra đầu ra. Không có luồng người dùng tải video lên để dự đoán trong MVP đầu tiên.
- Q: Mô hình 10 từ phải đạt mức chất lượng tối thiểu nào trên tập kiểm thử gồm những người không xuất hiện trong tập huấn luyện? → A: Macro-F1 tối thiểu 80% và recall của từng từ tối thiểu 65%.

### Session 2026-10-22

- Q: Quang đã chọn những ý nghĩa nào cho phạm vi P0? → A: Giấy tờ (giấy), Đau bụng, Thuốc, Sốt, Nhận, Bạn (Ngôi thứ 2), Xin chào, Cảm ơn, Chờ (đợi), Sao chép.

### Session 2026-10-24

- Q: Bảng `user` trong database cần đại diện cho đối tượng nào? → A: Chỉ thành viên nội bộ; MVP không có tài khoản người dùng cuối, lịch sử nhận diện hoặc database runtime. Sau khi đánh giá, phạm vi database được bỏ và chỉ cập nhật API contract.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nhận diện một ký hiệu (Priority: P1)

Một người dùng thực hiện một ký hiệu riêng lẻ trước camera. ViSign phân tích lần thực hiện và hiển thị
ý nghĩa bằng tiếng Việt cùng mức độ tin cậy.

**Why this priority**: Đây là giá trị cốt lõi và là luồng tối thiểu để ViSign có thể được trình diễn.

**Independent Test**: Chọn một ký hiệu thuộc phạm vi MVP, thực hiện một lần và xác nhận hệ thống trả
đúng chữ tiếng Việt, độ tin cậy và trạng thái chấp nhận.

**Acceptance Scenarios**:

1. **Given** người dùng đã cho phép sử dụng nguồn hình ảnh và chọn bắt đầu, **When** người dùng thực
   hiện một ký hiệu hợp lệ rồi kết thúc, **Then** hệ thống hiển thị ý nghĩa tiếng Việt, độ tin cậy và
   trạng thái đã nhận diện.
2. **Given** hai biến thể vùng miền khác nhau cùng mang một ý nghĩa, **When** mỗi biến thể được nhận
   diện, **Then** cả hai lần đều hiển thị cùng một nội dung tiếng Việt.
3. **Given** người dùng từ chối quyền camera hoặc nguồn hình ảnh không thể đọc, **When** bắt đầu nhận
   diện, **Then** hệ thống giải thích lỗi và hướng dẫn cách thử lại mà không bị treo.

---

### User Story 2 - Từ chối kết quả không chắc chắn (Priority: P1)

Một người dùng thực hiện động tác không thuộc phạm vi, không rõ ràng hoặc không có người trong khung
hình. ViSign không đoán bắt buộc mà trả về “Không nhận diện được”.

**Why this priority**: Một dự đoán sai nhưng được trình bày như chắc chắn có thể gây hiểu nhầm, đặc
biệt trong bối cảnh y tế hoặc hành chính.

**Independent Test**: Gửi một đoạn không có ký hiệu hợp lệ và xác nhận hệ thống không trả về một từ
thuộc từ điển như thể đó là kết quả chắc chắn.

**Acceptance Scenarios**:

1. **Given** độ tin cậy thấp hơn ngưỡng chấp nhận, **When** hệ thống hoàn thành phân tích, **Then** kết
   quả là “Không nhận diện được” và trạng thái không được chấp nhận.
2. **Given** đoạn ghi hình quá ngắn, quá dài, không có người hoặc tay ra khỏi khung, **When** người dùng
   gửi yêu cầu, **Then** hệ thống trả thông báo cụ thể và cho phép thử lại.
3. **Given** hệ thống nhận diện không sẵn sàng, **When** người dùng gửi một lần nhận diện, **Then** giao
   diện thông báo dịch vụ chưa sẵn sàng và không hiển thị dự đoán giả.
4. **Given** frontend gọi sai đường dẫn hoặc sai phương thức API, **When** backend trả lỗi định tuyến,
   **Then** giao diện hiển thị thông báo tiếng Việt ổn định, không lộ thông báo framework và không tự
   gửi lại video; đường dẫn chỉ khác dấu gạch chéo được chuẩn hóa mà không đổi phương thức request.

---

### User Story 3 - Đánh giá chất lượng bản MVP (Priority: P2)

Thành viên nhóm hoặc người đánh giá có thể xác định bản ViSign đang dùng tập từ nào, phiên bản mô hình
nào và chất lượng đã được kiểm thử ra sao trước khi chấp nhận bản demo.

**Why this priority**: Demo chỉ đáng tin cậy khi kết quả có thể truy về phạm vi dữ liệu và bằng chứng
đánh giá, thay vì dựa trên một vài ví dụ thuận lợi.

**Independent Test**: Kiểm tra một bản phát hành và xác nhận có danh sách ý nghĩa hỗ trợ, phiên bản dữ
liệu, phiên bản mô hình, chỉ số đánh giá và ngày đánh giá.

**Acceptance Scenarios**:

1. **Given** một bản mô hình được đề xuất cho MVP, **When** người đánh giá xem thông tin bản phát hành,
   **Then** họ thấy phạm vi từ vựng, phiên bản dữ liệu, cách chia tập và các chỉ số bắt buộc.
2. **Given** dữ liệu kiểm thử có người thực hiện mới, **When** chạy đánh giá, **Then** báo cáo tách riêng
   kết quả này và không trộn mẫu cùng phiên quay giữa huấn luyện và kiểm thử.
3. **Given** model đầy đủ 10 ý nghĩa chưa huấn luyện xong, **When** frontend và backend cần tích hợp,
   **Then** hệ thống có thể dùng fixture hoặc pilot model qua cùng contract, công bố đúng tập ý nghĩa
   đang hỗ trợ và luôn giữ `demoReady=false` cho đến khi full model vượt qua mọi quality gate.

### Edge Cases

- Camera bị từ chối quyền, bị thiết bị khác chiếm dụng hoặc mất kết nối giữa lần ghi.
- Đoạn ghi hình không có người, có nhiều người, tay rời khung hoặc khuôn mặt/cơ thể bị che khuất.
- Đoạn ghi hình quá ngắn, quá dài, sai định dạng hoặc hỏng.
- Người dùng thực hiện ký hiệu không thuộc phạm vi MVP hoặc chuyển tiếp giữa hai ký hiệu.
- Hai lớp vùng miền có cùng ý nghĩa nhưng độ tin cậy gần nhau.
- Dịch vụ nhận diện hoặc bản mô hình chưa sẵn sàng.
- Mạng chậm hoặc yêu cầu bị gián đoạn trước khi có kết quả.
- Nguồn dữ liệu bị phát hiện sai nhãn, không phải VSL hoặc không rõ quyền sử dụng.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST xử lý một ký hiệu riêng lẻ trong mỗi lần nhận diện; hội thoại liên tục nằm
  ngoài phạm vi MVP này.
- **FR-002**: Phạm vi phát hành đầu tiên MUST hỗ trợ đúng 10 ý nghĩa P0 đã đóng băng trong
  `data/manifests/p0-meanings.csv`: Giấy tờ (giấy), Đau bụng, Thuốc, Sốt, Nhận, Bạn (Ngôi thứ 2),
  Xin chào, Cảm ơn, Chờ (đợi) và Sao chép. Hai mươi ý nghĩa còn lại thuộc giai đoạn mở rộng sau khi
  pipeline 10 từ đạt cổng chất lượng.
- **FR-003**: Sản phẩm MVP MUST nhận đầu vào dự đoán trực tiếp từ camera. Video có sẵn MUST chỉ đi
  qua pipeline dữ liệu để huấn luyện và đánh giá; giao diện người dùng tải video lên để dự đoán nằm
  ngoài phạm vi phát hành đầu tiên.
- **FR-004**: Người dùng MUST có thể chủ động bắt đầu, kết thúc, gửi hoặc hủy một lần nhận diện.
- **FR-005**: Hệ thống MUST ánh xạ mọi lớp ký hiệu được hỗ trợ về đúng nội dung tiếng Việt; mã lớp và
  vùng miền không được hiển thị như kết quả chính cho người dùng.
- **FR-006**: Hệ thống MUST ưu tiên biến thể TP.HCM và MAY hỗ trợ biến thể vùng khác khi động tác khác
  và nguồn dữ liệu phù hợp.
- **FR-007**: Hệ thống MUST trả về nội dung tiếng Việt, độ tin cậy và trạng thái chấp nhận cho mỗi lần
  phân tích thành công.
- **FR-008**: Hệ thống MUST trả “Không nhận diện được” khi quyết định chấp nhận không đạt tiêu chí đã
  công bố hoặc đầu vào không đủ điều kiện; hệ thống MUST NOT buộc chọn một từ.
- **FR-009**: Hệ thống MUST phân biệt lỗi request, định dạng không hỗ trợ, clip không giải mã được,
  dịch vụ đang bận, quyền thiết bị, model chưa sẵn sàng và kết quả không chắc chắn bằng mã lỗi ổn định
  cùng thông báo dễ hiểu.
- **FR-010**: Giao diện MUST hiển thị cảnh báo rằng ViSign là sản phẩm thử nghiệm, kết quả có thể không
  chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.
- **FR-011**: Hệ thống MUST NOT lưu video nhận diện của người dùng sau khi trả kết quả nếu chưa có sự
  đồng ý rõ ràng.
- **FR-012**: Mỗi mẫu huấn luyện được chấp nhận MUST có ý nghĩa, nhãn lớp, vùng miền, nguồn, điều kiện
  sử dụng và trạng thái xác minh.
- **FR-013**: Hệ thống MUST loại khỏi dữ liệu được phê duyệt các mẫu sai nhãn, không phải VSL hoặc
  không rõ quyền sử dụng.
- **FR-014**: Mỗi bản mô hình được chấp nhận MUST gắn với phiên bản dữ liệu, extractor/feature schema,
  danh sách lớp, cách chia tập, ngày đánh giá và báo cáo gồm accuracy, precision, recall, Macro-F1,
  confusion matrix, latency cùng kết quả signer-held-out.
- **FR-015**: Quality gate chính thức MUST dùng tập kiểm thử tách theo `signerId` ẩn danh và gồm người
  không xuất hiện trong train/validation. Split theo `recordingSessionId` chỉ được dùng cho pilot hoặc
  phát triển khi không xác định được signer và MUST NOT được trình bày là bằng chứng unseen-signer.
- **FR-016**: Bản MVP MUST đạt Macro-F1 tối thiểu 80% và recall của từng ý nghĩa tối thiểu 65% trên
  tập kiểm thử tách theo người thực hiện để được chấp nhận cho demo.
- **FR-017**: Đăng nhập, lịch sử nhận diện, chuyển văn bản thành giọng nói, chuyển văn bản thành ký
  hiệu và nhận diện chuỗi câu MUST nằm ngoài phạm vi MVP này.
- **FR-018**: Hệ thống MUST cho phép thay thế `fixture`, `pilot` và `full` model artifact qua cùng
  predictor/API contract. Fixture và pilot MUST công bố đúng tập ý nghĩa đang hỗ trợ, MUST hiển thị là
  bản tích hợp nội bộ và MUST NOT được đánh dấu `demoReady=true`; chỉ full model đủ 10 ý nghĩa và đạt
  FR-016 mới được phát hành làm model demo.
- **FR-019**: Mọi API response MUST trả `X-Request-ID`; prediction thành công MAY trả phân rã thời gian
  `decode/extract/infer` và chỉ báo chất lượng đầu vào `handsDetectedRatio/frameCount`. Các trường chẩn
  đoán này MUST NOT thay thế trạng thái `accepted`, MUST NOT chứa frame/landmark và MUST NOT được persist.
- **FR-020**: API MUST trả error envelope ổn định có cùng request ID cho route không tồn tại và phương
  thức không được hỗ trợ; redirect chuẩn hóa đường dẫn MUST giữ nguyên phương thức và body. Giao diện
  MUST dùng đường dẫn chuẩn, MUST NOT hiển thị raw framework message và MUST phân biệt lỗi tương thích
  API với camera permission hoặc kết quả nhận diện bị từ chối. `403` chỉ được dùng khi có chính sách
  phân quyền thật; cache validation chỉ được bật sau khi contract invalidation được công bố.

### Key Entities *(include if feature involves data)*

- **Ý nghĩa tiếng Việt**: Nội dung hiển thị cho người dùng, ví dụ “Xin chào” hoặc “Đau bụng”; một ý
  nghĩa có thể liên kết với nhiều lớp ký hiệu.
- **Lớp ký hiệu**: Một động tác ký hiệu khác biệt dùng để nhận diện, gồm mã lớp, ý nghĩa đích, vùng
  miền và trạng thái xác minh.
- **Mẫu ký hiệu**: Một đoạn ghi hình hoặc đặc trưng đã trích xuất, gồm nguồn, người thực hiện ẩn danh,
  phiên quay, quyền sử dụng, nhãn và trạng thái kiểm duyệt.
- **Lần nhận diện**: Một lần người dùng cung cấp đầu vào, gồm trạng thái xử lý, kết quả tiếng Việt,
  độ tin cậy, trạng thái chấp nhận và mã lỗi nếu có; video không được lưu mặc định.
- **Phiên bản mô hình**: Bản nhận diện có định danh, phiên bản dữ liệu, danh sách lớp, ngưỡng chấp
  nhận, chỉ số đánh giá và ngày tạo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ít nhất 90% người thử nghiệm có thể hoàn thành một lần nhận diện hợp lệ mà không cần
  người phát triển hướng dẫn trực tiếp.
- **SC-002**: Sau khi người dùng kết thúc và gửi ký hiệu, 95% lần thử hợp lệ hiển thị kết quả hoặc lỗi
  có thể xử lý trong không quá 3 giây trên môi trường demo đã công bố.
- **SC-003**: 100% lần thử không đạt decision rule đã công bố hiển thị “Không nhận diện được” thay vì
  một từ được khẳng định chắc chắn; báo cáo MUST nêu rõ rule, threshold và tập đánh giá đã dùng.
- **SC-004**: Bản mô hình demo đạt ngưỡng chất lượng được chốt trong FR-016 trên tập kiểm thử tách theo
  người thực hiện và có báo cáo theo từng lớp.
- **SC-005**: 100% mẫu dữ liệu được dùng cho bản mô hình demo có nguồn và trạng thái quyền sử dụng;
  mọi mẫu chưa được chuyên gia xác minh được đánh dấu rõ.
- **SC-006**: Không có video nhận diện của người dùng được lưu sau khi trả kết quả trong luồng mặc định.
- **SC-007**: Luồng demo bắt buộc chạy thành công với ít nhất ba ý nghĩa thuộc các nhóm giao tiếp, y tế
  và hành chính, đồng thời có một lần thử không hợp lệ được từ chối đúng.
- **SC-008**: 100% kiểm thử route không tồn tại, phương thức không hợp lệ và chuẩn hóa trailing slash
  trả đúng trạng thái, giữ correlation ID cần thiết và hiển thị stable Vietnamese copy thay vì raw
  server/framework text.
## Assumptions

- MVP nhận diện từng ký hiệu riêng lẻ, không diễn giải ngữ pháp hoặc chuỗi câu.
- Video raw material được dùng để xây dựng tập huấn luyện và đánh giá; camera trực tiếp là nguồn đầu
  vào duy nhất của luồng dự đoán dành cho người dùng trong MVP đầu tiên.
- Người dùng mục tiêu là người sử dụng VSL và người nghe cần hiểu một số ý nghĩa thiết yếu trong bối
  cảnh giao tiếp, y tế và hành chính.
- Biến thể TP.HCM được ưu tiên; biến thể vùng khác vẫn có thể được giữ thành lớp riêng và ánh xạ về
  cùng một nội dung tiếng Việt.
- Một mẫu từ nguồn trực tuyến có thể được dùng ở giai đoạn thử nghiệm nếu quyền sử dụng phù hợp, nhưng
  phải mang trạng thái chưa xác minh cho đến khi được người có chuyên môn đối chiếu.
- Danh sách 10 ý nghĩa P0 đã được Quang chốt ngày 2026-10-22; việc chốt danh mục không đồng nghĩa các
  video mẫu đã được duyệt. Từng mẫu vẫn phải qua lọc nhãn, kiểm tra quyền sử dụng và phân tích độ phủ.
- Mức 20–30 mẫu mỗi lớp và 3–5 signer chỉ là planning floor để chạy pilot, không phải bằng chứng dữ
  liệu đã đủ; quyết định full training dựa trên coverage theo meaning × signer và split audit.
- Bản demo có thể chạy cục bộ nếu lựa chọn này ổn định hơn triển khai cloud.
- Nhóm chuẩn bị bản chạy cục bộ, bộ dữ liệu kiểm thử và bằng chứng đánh giá làm phương án dự phòng
  cho buổi trình diễn.
