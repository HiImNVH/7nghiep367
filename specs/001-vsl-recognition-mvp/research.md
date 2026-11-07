# Research: ViSign VSL Recognition MVP

## 1. Kiến trúc đầu vào camera

**Decision**: Trình duyệt ghi một đoạn ký hiệu ngắn do người dùng chủ động bắt đầu/kết thúc, gửi một
request `multipart/form-data` đến inference API và chờ một kết quả duy nhất.

**Rationale**: Luồng này đúng phạm vi ký hiệu riêng lẻ, dễ lặp lại trong kiểm thử và ít trạng thái hơn
streaming liên tục. FastAPI hỗ trợ file tạm kiểu spooled thông qua `UploadFile`, phù hợp để truyền đoạn
camera mà không giữ toàn bộ file lớn trong bộ nhớ.

**Alternatives considered**:

- WebSocket streaming: loại vì tăng độ phức tạp đồng bộ frame và không cần cho MVP ký hiệu riêng lẻ.
- Suy luận hoàn toàn trong trình duyệt: loại vì tạo thêm bước chuyển đổi model và hai runtime AI.
- Người dùng tải video lên: loại theo quyết định phạm vi; video chỉ dành cho pipeline dữ liệu.

**Source**: [FastAPI request files](https://fastapi.tiangolo.com/tutorial/request-files/)

## 2. Trích xuất đặc trưng

**Decision**: Dùng MediaPipe Tasks Holistic Landmarker trong chế độ video cho raw material và đoạn
camera, giữ landmark tay trái, tay phải, pose và một tập con landmark khuôn mặt cần thiết.

**Rationale**: API chính thức hỗ trợ ảnh, video và live stream, nhận timestamp tăng dần và trả landmark
toàn thân. Cùng một bộ trích xuất cho huấn luyện và suy luận giúp giảm training-serving skew.

**Alternatives considered**:

- Chỉ hand landmarks: loại vì VSL có thể phụ thuộc tư thế, vị trí tay so với cơ thể và nét mặt.
- Pixel-based video model: loại vì cần nhiều dữ liệu và tài nguyên hơn mức hackathon.
- Trộn nhiều landmark extractor: loại để giữ một ranh giới preprocessing duy nhất.

**Source**: [MediaPipe Holistic Landmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HolisticLandmarker)

## 3. Mô hình chuỗi

**Decision**: Baseline một GRU theo chuỗi landmark đã chuẩn hóa, với output softmax trên các lớp ký
hiệu và ngưỡng chấp nhận được hiệu chỉnh trên validation set.

**Rationale**: GRU xử lý trực tiếp chuỗi có độ dài thay đổi, có ít tham số hơn nhiều kiến trúc video
dựa trên pixel và đủ đơn giản để huấn luyện/giải thích trong MVP. PyTorch cung cấp GRU ổn định và hỗ
trợ packed variable-length sequences.

**Alternatives considered**:

- LSTM: khả thi nhưng nhiều tham số hơn; giữ làm baseline thay thế nếu GRU không đạt cổng.
- Transformer: hoãn đến khi dữ liệu lớn hơn và baseline chứng minh pipeline đúng.
- Random Forest trên vector gộp: có thể dùng sanity baseline nhưng không phải model demo chính vì làm
  mất thứ tự thời gian.

**Source**: [PyTorch GRU](https://docs.pytorch.org/docs/stable/generated/torch.nn.GRU.html)

## 4. Chuẩn hóa và chia dữ liệu

**Decision**: Chuẩn hóa tọa độ theo mốc vai/thân người, resample chuỗi về độ dài cấu hình, thêm mask
cho frame thiếu landmark; split train/validation/test theo `signerId`, và nếu thiếu danh tính thì theo
`recordingSessionId`.

**Rationale**: Chia ngẫu nhiên theo video sẽ làm rò rỉ đặc điểm người và phiên quay. Split theo người
đo khả năng tổng quát hóa đúng với ngưỡng đã chốt.

**Alternatives considered**:

- Random per-video split: loại vì nguy cơ leakage cao.
- Một độ dài cứng bằng cắt bỏ: loại vì có thể mất phần quan trọng của động tác.
- Dùng tên người thật: loại; manifest chỉ dùng mã ẩn danh.

## 5. Web stack

**Decision**: React + TypeScript trên Vite, dùng MediaDevices/MediaRecorder của trình duyệt, state cục
bộ cho một lần ghi và một API client sinh kiểu từ OpenAPI.

**Rationale**: Vite có template React TypeScript chính thức và cấu hình tối thiểu, phù hợp UI một màn
hình. TypeScript giảm sai lệch giữa contract và trạng thái UI.

**Alternatives considered**:

- Next.js: loại vì SSR, routing server và data framework không tạo giá trị cho một màn hình demo.
- Vanilla TypeScript: khả thi nhưng state permission/recording/upload/result dễ rối hơn.
- Mobile native: ngoài phạm vi web MVP.

**Source**: [Vite Getting Started](https://vite.dev/guide/)

## 6. API và kiểm thử

**Decision**: FastAPI/Pydantic với contract OpenAPI versioned; pytest/TestClient cho API và domain,
Vitest cho web unit, Playwright Chromium cho E2E camera giả lập và lỗi quyền.

**Rationale**: FastAPI tách validation contract khỏi inference adapter; TestClient cho phép kiểm thử
HTTP không cần server thật. Playwright có web-first assertions phù hợp luồng permission/loading/result.

**Alternatives considered**:

- Flask không schema: loại vì cần contract typed và lỗi ổn định.
- Chỉ kiểm thử thủ công: vi phạm cổng chất lượng và khó lặp lại trước demo.
- Kiểm thử E2E đa trình duyệt ngay MVP: hoãn; Chromium là target được công bố.

**Sources**: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/),
[Playwright Test](https://playwright.dev/docs/api/class-test)

## 7. Lưu trữ và quyền riêng tư

**Decision**: Không dùng database trong MVP. Raw material nằm ngoài repository; manifest và metadata
được version-control. Prediction upload dùng file tạm có giới hạn, luôn xóa trong `finally`; log chỉ
giữ request correlation ID, thời gian, model version, accepted và error code.

**Rationale**: MVP không có tài khoản hoặc lịch sử. File-based artifacts dễ audit và tránh thu thập
dữ liệu người dùng không cần thiết.

**Alternatives considered**:

- PostgreSQL: loại vì không có entity cần persistence trực tuyến.
- Lưu clip để cải thiện model: chỉ được thêm sau bằng consent flow có đặc tả riêng.
- Log payload/frame: loại vì rủi ro dữ liệu cá nhân.

## 8. Cổng model demo-ready

**Decision**: Model chỉ được đánh dấu `demoReady=true` khi macro-F1 ≥0.80, recall từng ý nghĩa ≥0.65,
test split không trùng người/phiên quay với train, model card đầy đủ và smoke inference vượt qua.

**Rationale**: Cổng kết hợp chất lượng tổng thể và sàn theo từng từ, tránh một vài lớp mạnh che lớp yếu.

**Alternatives considered**:

- Accuracy tổng thể: loại vì dễ che mất lớp ít mẫu.
- Chỉ demo thủ công: loại vì không lặp lại và dễ selection bias.
- Per-class recall 0.80: giữ làm mục tiêu P1, chưa dùng làm cổng MVP theo quyết định người dùng.

## 9. Fallback khi huấn luyện full model trễ

**Decision**: Dùng ba loại artifact có cùng predictor contract: `fixture` là predictor test double
xác định trước cho contract và E2E, `pilot` tối đa 3 ý nghĩa có dữ liệu tốt cho smoke training, và
`full` đúng 10 ý nghĩa P0 cho
phát hành. Fixture/pilot luôn có `demoReady=false`; chỉ full model vượt mọi gate mới được dùng cho demo
MVP chính thức.

**Rationale**: Frontend, backend, camera, cleanup, error handling và integration tests không cần chờ
quá trình thu thập dữ liệu hoặc train hoàn tất. Giữ chung feature schema, metadata envelope và API
contract làm cho việc nâng cấp artifact chỉ là thay cấu hình và restart API, tránh tạo nhánh code riêng
cho pilot. Fixture chỉ thay learned inference; request validation, cleanup, errors và privacy vẫn chạy.

**Alternatives considered**:

- Chờ full model rồi mới tích hợp: loại vì biến training thành blocker cho toàn nhóm.
- Cho pilot giả làm model MVP: loại vì vi phạm tính trung thực và quality gate.
- Tạo endpoint riêng cho pilot: loại vì làm tăng contract, test matrix và nguy cơ lệch frontend.
- Dùng model khác kiến trúc cho pilot: loại vì không kiểm chứng đúng pipeline GRU sẽ phát hành.

## 10. Decode WebM và timestamp

**Decision**: Đặt decode sau một `VideoDecoder` boundary. Dùng PyAV cho implementation MVP khi spike
trên laptop demo giải mã được toàn bộ clip kiểm thử Chrome/Edge, giữ PTS tăng đơn điệu và duration
trong sai số đã công bố. Nếu spike thất bại, thay adapter bằng FFmpeg CLI nhưng không đổi extractor.

**Rationale**: MediaRecorder WebM không đảm bảo duration header hữu ích, còn MediaPipe video mode cần
timestamp tăng dần. Tách decoder giúp lỗi container/codec không rò vào preprocessing/model.

**Alternatives considered**:

- `cv2.VideoCapture`: không chọn làm mặc định vì WebM VP8/VP9 phụ thuộc wheel/backend trên Windows.
- Tin `Content-Type` hoặc duration client: loại vì dữ liệu client không phải bằng chứng decode được.

## 11. Training-serving parity

**Decision**: `visign_ai.landmarks` là code path duy nhất cho extractor và sequence transform; API
import package này trực tiếp. `feature_schema.json` mô tả thứ tự landmark, normalization, resampling,
mask và extractor version. Golden clip→tensor test chạy trong cả AI và integration suite.

**Rationale**: Metadata version mà không có parity test không ngăn được training-serving skew.

## 12. Signer split và session fallback

**Decision**: Full demo gate chỉ chấp nhận test split theo `signerId` ẩn danh. Session-only split được
phép cho pilot/dev nhưng report phải gắn nhãn `session-only` và không được tuyên bố unseen-signer.

**Rationale**: Hai session khác nhau vẫn có thể thuộc cùng người; fallback session không chứng minh
khả năng tổng quát hóa sang signer mới.

## 13. Rejection strategy

**Decision**: Baseline phát hành bắt đầu bằng threshold có report negative/OOD riêng. Margin,
temperature scaling và lớp `NONE` là M1 experiments trên cùng split; chỉ phương án thắng A/B và không
làm suy giảm gate 10 meaning mới được đưa vào full model.

**Rationale**: Một lớp `NONE` nghèo đa dạng có thể tạo cảm giác an toàn sai. SC-003 chỉ chứng minh
decision rule, không chứng minh khả năng từ chối mọi động tác ngoài phân phối.

## 14. Các nâng cấp bị hoãn

**Decision**: Giữ npm/package-lock và mypy hiện có. Tailwind/shadcn, DVC/MLflow, alternative model,
ONNX, browser overlay, client-side extraction, Docker và cloud là M2 hoặc M1 có trigger; không nằm
trên critical path camera→API→model→text.

**Rationale**: Chúng không đóng lỗ hổng correctness đang chặn pilot và có thể làm phình MVP.

## 15. API diagnostics và request correlation

**Decision**: Áp dụng `X-Request-ID` tùy chọn ở request và bắt buộc echo ở mọi response. Prediction
response giữ `processingTimeMs` và MAY bổ sung `timingsMs {decode, extract, infer}` cùng
`qualityHints {handsDetectedRatio, frameCount}`. Các diagnostics không chứa frame/landmark, không
persist và không quyết định `accepted`. `CLIP_DECODE_FAILED` và `SERVICE_BUSY` là stable error codes;
busy response MAY kèm `Retry-After`. Không thêm endpoint `/predictions/landmarks` trong MVP.

**Rationale**: Correlation ID và breakdown giúp debug/benchmark mà không tạo history hoặc thu thập dữ
liệu sinh trắc. Trường optional giữ tương thích client; landmark endpoint bị hoãn vì sẽ tạo một input
contract và trust boundary mới trước khi MVP cần đến.

**Alternatives considered**:

- Lưu prediction diagnostics vào SQL: loại vì MVP không có history và không cần persistence runtime.
- Trả raw landmarks trong response: loại vì tăng payload, privacy surface và coupling với extractor.
- Dùng `timingsMs` để quyết định accepted: loại vì latency không phản ánh độ tin cậy phân loại.

## 16. Branch-first integration và bằng chứng hoàn thành

**Decision**: `main` giữ Spec Kit và task checkbox. Code trên nhánh vai trò được ghi là `BRANCH` hoặc
`PARTIAL`, không đánh dấu task hoàn thành cho đến khi review, merge và chạy lại test trên `main`.

**Rationale**: Các nhánh hiện có mức trưởng thành khác nhau và được tạo từ các mốc không đồng nhất.
Đóng task theo tuyên bố bàn giao sẽ che mất xung đột contract và thiếu bằng chứng end-to-end.

**Alternatives considered**:

- Đánh dấu hoàn thành theo file hiện có trên bất kỳ nhánh nào: loại vì không tạo được baseline chạy lại.
- Merge toàn bộ nhánh tích hợp một lần: loại vì khó review và khó truy task owner khi regression.

## 17. Công cụ Admin/train-model

**Decision**: Giữ công cụ kiểm tra clip, preflight, pilot job và W&B history thành một user story nội
bộ riêng. API chỉ bật khi có `VISIGN_ADMIN_TOKEN`, clip inspect được dọn sau response, mỗi lúc chỉ có
một job active, và pilot luôn `demoReady=false`.

**Rationale**: Công cụ đang có giúp nhóm lặp nhanh pipeline thật, nhưng public hóa hoặc gộp với API
người dùng sẽ mở rộng trust boundary và dễ làm pilot bị hiểu nhầm là bản phát hành.

**Alternatives considered**:

- Bỏ toàn bộ công cụ vì ngoài MVP user flow: loại vì mất bằng chứng vận hành hữu ích đã có.
- Đưa admin routes vào public `/api/v1`: loại vì contract, auth và retention policy khác nhau.
- Dùng pilot metrics để tự bật `demoReady`: loại vì vi phạm FR-016 và full 10-meaning gate.
