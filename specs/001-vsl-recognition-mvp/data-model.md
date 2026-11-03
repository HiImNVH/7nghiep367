# Data Model: ViSign VSL Recognition MVP

## Meaning

Ý nghĩa tiếng Việt hiển thị cho người dùng.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `meaningId` | string | yes | Upper snake case, duy nhất, ví dụ `XIN_CHAO` |
| `displayText` | string | yes | Tiếng Việt, không rỗng |
| `category` | enum | yes | `basic`, `medical`, `administrative` |
| `priority` | enum | yes | `P0` cho 10 ý nghĩa MVP; `P1` cho danh sách mở rộng |
| `active` | boolean | yes | Chỉ `true` mới xuất hiện trong model hiện hành |

**Relationships**: Một Meaning có một hoặc nhiều SignClass.

## SignClass

Một động tác khác biệt mà model phân loại, ánh xạ về một Meaning.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `classLabel` | string | yes | Duy nhất, upper snake case, gồm meaning và variant |
| `meaningId` | string | yes | Phải tham chiếu Meaning tồn tại |
| `region` | enum | yes | `HCM`, `HN`, `HP`, `OTHER`, `UNKNOWN` |
| `variantName` | string | yes | Tên ổn định trong manifest |
| `verified` | boolean | yes | `false` cho đến khi được người có chuyên môn xác minh |
| `active` | boolean | yes | Chỉ class đủ dữ liệu mới được huấn luyện |

**Uniqueness**: `classLabel` duy nhất; cặp `meaningId + region + variantName` duy nhất.

## SignSample

Metadata cho một raw video hoặc một artifact landmark đã xử lý.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `sampleId` | string | yes | Duy nhất, không chứa tên người thật |
| `classLabel` | string | yes | Phải tham chiếu SignClass tồn tại |
| `signerId` | string | conditional | Mã ẩn danh; bắt buộc với mọi mẫu dùng cho full quality gate |
| `recordingSessionId` | string | yes | Chống trùng phiên; không thay thế signerId cho full gate |
| `sourceUri` | string | yes | URL nguồn hoặc mã bộ dữ liệu; không nhúng credential |
| `licenseStatus` | enum | yes | `approved`, `restricted`, `unknown` |
| `verificationStatus` | enum | yes | `verified`, `unverified`, `rejected` |
| `rejectionReason` | enum/null | conditional | Bắt buộc khi `rejected` |
| `rawPath` | string | yes | Path tương đối trong kho dữ liệu cục bộ, không commit video |
| `landmarkPath` | string/null | no | Path artifact đã trích xuất |
| `durationMs` | integer | yes | >0 và nằm trong giới hạn pipeline |
| `frameCount` | integer | yes | >0 |
| `split` | enum/null | no | `train`, `validation`, `test`; gán sau data audit |

**State transitions**:

```text
unverified -> verified
unverified -> rejected
verified   -> rejected  (khi audit phát hiện sai)
```

Mẫu `licenseStatus != approved` hoặc `verificationStatus == rejected` không được vào model release.
Mẫu thiếu `signerId` MAY dùng cho pilot/dev với session split nhưng MUST NOT nằm trong test set dùng
để chứng minh unseen-signer quality gate.

## FeatureSchema

Contract bất biến giữa extraction, training và serving; lưu trong `feature_schema.json`.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `featureSchemaVersion` | string | yes | Tăng khi shape/thứ tự/transform thay đổi |
| `extractorVersion` | string | yes | Phiên bản MediaPipe và hash model bundle |
| `landmarkOrder` | string[] | yes | Có thứ tự, không trùng, dùng chung train/API |
| `normalization` | object | yes | Origin, scale và handedness policy tường minh |
| `targetFrameCount` | integer | yes | >0; cùng giá trị khi train/serve |
| `resampling` | string | yes | Tên thuật toán và policy timestamp |
| `missingMaskSchema` | string[] | yes | Khớp landmark groups |
| `velocityEnabled` | boolean | yes | Nếu đổi phải tăng schema version |

**Integrity**: Training CLI và API MUST load cùng file; mismatch làm artifact không sẵn sàng.

## LandmarkSequence

Chuỗi đặc trưng sinh từ SignSample; không chứa pixel video.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `sampleId` | string | yes | Một-một với SignSample đã xử lý |
| `extractorVersion` | string | yes | Phiên bản MediaPipe/model bundle |
| `featureSchemaVersion` | string | yes | Khớp model input schema |
| `timestampsMs` | integer[] | yes | Tăng đơn điệu |
| `features` | float[][] | yes | Kích thước frame nhất quán |
| `missingMask` | boolean[][] | yes | Cùng shape landmark groups |
| `normalization` | string | yes | Tên cấu hình chuẩn hóa |

## ModelVersion

Metadata đi kèm model artifact.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `modelVersion` | string | yes | Duy nhất, immutable |
| `artifactKind` | enum | yes | `fixture`, `pilot`, `full`; chỉ `full` có thể demo-ready |
| `datasetVersion` | string | yes | Hash hoặc tag manifest |
| `featureSchemaVersion` | string | yes | Phải khớp request preprocessing |
| `extractorVersion` | string | yes | Phải khớp FeatureSchema đã đóng gói |
| `classLabels` | string[] | yes | Danh sách có thứ tự, không trùng |
| `meaningMap` | object | yes | Mỗi classLabel ánh xạ đúng một Meaning |
| `acceptanceThreshold` | number | yes | Trong [0,1], hiệu chỉnh trên validation |
| `accuracy` | number/null | yes | Null cho fixture; trong [0,1] khi đã evaluation |
| `macroF1` | number/null | yes | Null cho fixture; ≥0.80 với full để `demoReady=true` |
| `perMeaningPrecision` | object/null | yes | Null cho fixture; từng value trong [0,1] |
| `perMeaningRecall` | object/null | yes | Null cho fixture; mọi P0 meaning ≥0.65 với full |
| `evaluatedAt` | datetime/null | yes | Null cho fixture; nếu có thì ISO 8601 UTC |
| `demoReady` | boolean | yes | Chỉ true khi `artifactKind=full`, đủ 10 meaning và mọi gate đạt |

**Fallback invariants**:

- `fixture` và `pilot` luôn có `demoReady=false`.
- `pilot` hỗ trợ tối đa 3 meaning đã duyệt; `full` phải hỗ trợ đúng 10 meaning P0.
- Mọi artifact dùng cùng `featureSchemaVersion` và predictor interface để có thể đổi bằng cấu hình.
- API/UI phải công bố đúng `artifactKind` và tập meaning đang hỗ trợ, không suy diễn pilot thành full.
- Artifact sai extractor/feature schema MUST fail closed và rollback.

**M1 candidate fields**: `configHash`, `artifactChecksums` và warm-up status chỉ được thêm vào schema
khi Huy duyệt M1 artifact-integrity trigger; chúng chưa phải contract bắt buộc của MVP hiện tại.

## PredictionRequest

Đối tượng tạm thời tại ranh giới API; không persist.

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `requestId` | UUID | yes | Server tạo |
| `clip` | binary | yes | MIME allowlist, giới hạn kích thước và thời lượng |
| `contentType` | string | yes | `video/webm` hoặc format camera được công bố |
| `receivedAt` | datetime | yes | ISO 8601 UTC |

Caller MAY gửi UUID qua `X-Request-ID`; server tạo UUID khi thiếu và MUST echo giá trị hiệu lực trong
mọi response header. ID này chỉ phục vụ correlation, không tạo prediction history.

**Lifecycle**: `received -> validated -> processing -> completed/failed -> deleted`.

## PredictionResponse

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `requestId` | UUID | yes | Correlates log without storing video |
| `text` | string | yes | Tiếng Việt hoặc “Không nhận diện được” |
| `classLabel` | string/null | yes | Field luôn có; value null khi rejected |
| `confidence` | number | yes | Trong [0,1] |
| `accepted` | boolean | yes | False dưới threshold/invalid signal |
| `modelVersion` | string | yes | Model đã xử lý request |
| `processingTimeMs` | integer | yes | ≥0 |
| `timingsMs` | PredictionTimings/null | no | `decode`, `extract`, `infer` đều là integer ≥0 |
| `qualityHints` | PredictionQualityHints/null | no | `handsDetectedRatio` trong [0,1], `frameCount` ≥1 |

`timingsMs` và `qualityHints` là diagnostics tùy chọn, không tham gia quyết định `accepted`, không chứa
frame/landmark và không được persist. Lỗi dùng `ErrorEnvelope` riêng theo HTTP status, không trộn vào
`PredictionResponse` thành công.

## ErrorEnvelope

| Field | Type | Required | Validation |
|------|------|----------|------------|
| `code` | enum | yes | Stable code từ contract |
| `message` | string | yes | Thông báo tiếng Việt cho người dùng ViSign |
| `requestId` | UUID | yes | Dùng đối chiếu log |
