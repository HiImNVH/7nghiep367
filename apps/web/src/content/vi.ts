import type { ArtifactKind, ErrorCode } from '../types/inference-api';

export interface ErrorCopy {
  title: string;
  guidance: string;
}

export const apiErrors = {
  INVALID_REQUEST: {
    title: 'Yêu cầu không hợp lệ',
    guidance: 'Hãy quay lại một ký hiệu rồi gửi lại.',
  },
  UNSUPPORTED_MEDIA_TYPE: {
    title: 'Định dạng ghi hình chưa được hỗ trợ',
    guidance: 'Hãy dùng Chrome hoặc Edge và quay lại bằng camera của ứng dụng.',
  },
  CLIP_TOO_LARGE: {
    title: 'Đoạn ghi hình vượt giới hạn dung lượng',
    guidance: 'Hãy quay đoạn ngắn hơn, chỉ thực hiện một ký hiệu.',
  },
  CLIP_TOO_SHORT: {
    title: 'Đoạn ghi hình quá ngắn',
    guidance: 'Hãy thực hiện trọn một ký hiệu trước khi dừng quay.',
  },
  CLIP_TOO_LONG: {
    title: 'Đoạn ghi hình quá dài',
    guidance: 'Hãy quay lại và dừng sau khi thực hiện xong một ký hiệu.',
  },
  NO_PERSON_DETECTED: {
    title: 'Không thấy người trong khung hình',
    guidance: 'Hãy đứng ở nơi đủ sáng, để phần thân trên và hai tay trong khung hình rồi quay lại.',
  },
  INSUFFICIENT_LANDMARKS: {
    title: 'Chưa thấy rõ động tác',
    guidance: 'Hãy giữ hai tay và phần thân trên trong khung hình, tránh che khuất rồi quay lại.',
  },
  CLIP_DECODE_FAILED: {
    title: 'Không đọc được đoạn ghi hình',
    guidance: 'Hãy quay lại bằng camera. Nếu vẫn gặp lỗi, hãy tải lại trang.',
  },
  SERVICE_BUSY: {
    title: 'Hệ thống đang bận',
    guidance: 'Hãy chờ một lát rồi thử lại.',
  },
  MODEL_NOT_READY: {
    title: 'Dịch vụ nhận diện chưa sẵn sàng',
    guidance: 'Hãy chờ hệ thống sẵn sàng rồi thử lại.',
  },
  PREDICTION_FAILED: {
    title: 'Không thể hoàn tất nhận diện',
    guidance: 'Hãy thử lại. Nếu lỗi tiếp tục, hãy cung cấp mã yêu cầu cho nhóm hỗ trợ.',
  },
} as const satisfies Record<ErrorCode, ErrorCopy>;

export const cameraErrors = {
  NotAllowedError: {
    title: 'Chưa có quyền sử dụng camera',
    guidance: 'Hãy cho phép camera trong cài đặt của trang trên trình duyệt rồi thử lại.',
  },
  NotFoundError: {
    title: 'Không tìm thấy camera',
    guidance: 'Hãy kết nối hoặc bật camera rồi thử lại.',
  },
  NotReadableError: {
    title: 'Không mở được camera',
    guidance: 'Hãy đóng ứng dụng khác đang dùng camera và kiểm tra thiết bị rồi thử lại.',
  },
  OverconstrainedError: {
    title: 'Camera không hỗ trợ cấu hình ghi hình',
    guidance: 'Hãy thử camera khác hoặc kiểm tra cài đặt thiết bị.',
  },
  disconnected: {
    title: 'Camera đã mất kết nối',
    guidance: 'Hãy kết nối lại camera rồi quay lại ký hiệu.',
  },
  unsupported: {
    title: 'Trình duyệt chưa hỗ trợ ghi hình',
    guidance: 'Hãy mở ứng dụng bằng Chrome hoặc Edge.',
  },
  insecureContext: {
    title: 'Không thể truy cập camera tại địa chỉ này',
    guidance: 'Hãy mở ứng dụng qua localhost hoặc địa chỉ HTTPS được nhóm cung cấp.',
  },
  recordingFailed: {
    title: 'Không ghi được đoạn camera',
    guidance: 'Hãy kiểm tra camera rồi bắt đầu quay lại.',
  },
  unknown: {
    title: 'Camera gặp lỗi',
    guidance: 'Hãy kiểm tra quyền camera và thiết bị rồi thử lại.',
  },
} as const satisfies Record<string, ErrorCopy>;

export const requestErrors = {
  network: {
    title: 'Không kết nối được dịch vụ',
    guidance: 'Hãy kiểm tra kết nối tới dịch vụ nhận diện rồi thử lại.',
  },
  timeout: {
    title: 'Chờ kết quả quá lâu',
    guidance: 'Hãy thử lại khi dịch vụ phản hồi ổn định.',
  },
  invalidResponse: {
    title: 'Không đọc được kết quả từ dịch vụ',
    guidance: 'Hãy thử lại. Nếu lỗi tiếp tục, hãy báo cho nhóm hỗ trợ.',
  },
  unknown: {
    title: 'Đã xảy ra lỗi',
    guidance: 'Hãy thử lại. Nếu lỗi tiếp tục, hãy báo cho nhóm hỗ trợ.',
  },
} as const satisfies Record<string, ErrorCopy>;

export const modelNotices = {
  fixture: 'Chế độ kiểm thử tích hợp: kết quả được tạo sẵn để kiểm tra ứng dụng, chưa phải kết quả nhận diện bằng model thật.',
  pilot: 'Model thử nghiệm giới hạn: chỉ hỗ trợ các ý nghĩa được liệt kê, chưa sẵn sàng cho demo MVP chính thức.',
  full: 'Model đầy đủ đang được kiểm chứng, chưa sẵn sàng cho demo MVP chính thức.',
} as const satisfies Record<ArtifactKind, string>;

export const vi = {
  appName: 'ViSign',
  title: 'Nhận diện ngôn ngữ ký hiệu Việt Nam',
  instructions: 'Đặt camera ở nơi đủ sáng, để phần thân trên và hai tay trong khung hình. Mỗi lần quay chỉ thực hiện một ký hiệu.',
  recordingInstructions: 'Bắt đầu quay, thực hiện ký hiệu rồi dừng. Bạn có thể gửi để nhận diện hoặc hủy đoạn vừa quay.',
  disclaimer: 'ViSign là sản phẩm thử nghiệm. Kết quả có thể không chính xác và không thay thế phiên dịch viên chuyên nghiệp trong tình huống quan trọng.',
  privacy: 'Đoạn camera được gửi tới dịch vụ nhận diện để xử lý tạm thời và được xóa sau khi xử lý.',
  actions: {
    enableCamera: 'Bật camera',
    startRecording: 'Bắt đầu quay',
    stopRecording: 'Dừng quay',
    submit: 'Gửi nhận diện',
    cancelRecording: 'Hủy đoạn quay',
    cancelRequest: 'Hủy yêu cầu',
    retry: 'Thử lại',
    recordAgain: 'Quay lại',
    reset: 'Bắt đầu lượt mới',
  },
  status: {
    idle: 'Bật camera để bắt đầu.',
    requestingPermission: 'Đang chờ quyền sử dụng camera…',
    ready: 'Camera đã sẵn sàng.',
    recording: 'Đang quay ký hiệu…',
    recorded: 'Đã quay xong. Bạn có thể gửi hoặc quay lại.',
    submitting: 'Đang gửi và nhận diện…',
    cancelled: 'Đã hủy lượt nhận diện.',
    loadingModel: 'Đang đọc thông tin model…',
    modelUnavailable: 'Chưa lấy được phạm vi nhận diện. Hãy thử lại.',
  },
  result: {
    heading: 'Kết quả nhận diện',
    accepted: 'Đã nhận diện',
    rejected: 'Không nhận diện được',
    retryGuidance: 'Hãy kiểm tra ký hiệu có thuộc phạm vi hỗ trợ, giữ tay rõ trong khung hình rồi thử lại.',
    confidence: 'Độ tin cậy',
    requestId: 'Mã yêu cầu',
  },
  model: {
    supportedMeanings: 'Các ý nghĩa đang hỗ trợ',
    version: 'Phiên bản model',
    demoReady: 'Model đã sẵn sàng cho demo MVP',
    notices: modelNotices,
  },
  a11y: {
    cameraPreview: 'Hình ảnh xem trước từ camera',
    cameraControls: 'Điều khiển ghi hình ký hiệu',
    recognitionStatus: 'Trạng thái nhận diện',
    recognitionResult: 'Kết quả nhận diện ký hiệu',
    error: 'Thông báo lỗi và hướng dẫn thử lại',
    modelInfo: 'Thông tin và phạm vi của model đang sử dụng',
  },
  errors: { api: apiErrors, camera: cameraErrors, request: requestErrors },
} as const;
