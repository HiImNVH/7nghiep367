import { useRef } from 'react';
import { vi } from '../content/vi';
import { UiIcon } from './UiIcon';

export function CameraHelp({ recordingEnabled = false, recognitionEnabled = false }: { recordingEnabled?: boolean; recognitionEnabled?: boolean }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  return (
    <>
      <button className="help-button" ref={trigger} onClick={() => dialog.current?.showModal()}><UiIcon name="help" /><span>Hướng dẫn</span></button>
      <dialog className="help-dialog" ref={dialog} aria-labelledby="help-heading" onClose={() => trigger.current?.focus()} onKeyDown={event => {
        if (event.key !== 'Tab') return;
        const buttons = dialog.current?.querySelectorAll<HTMLButtonElement>('button:not([disabled])');
        const first = buttons?.[0];
        const last = buttons?.[buttons.length - 1];
        if (!first || !last) return;
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }}>
        <div className="dialog-heading"><h2 id="help-heading">{recordingEnabled || recognitionEnabled ? 'Một ký hiệu, một lần nhận diện' : 'Đặt camera đúng khung hình'}</h2><button className="icon-button" aria-label="Đóng hướng dẫn" onClick={() => dialog.current?.close()}><UiIcon name="close" /></button></div>
        <p className="dialog-intro">Chỉ cần camera và một chút ánh sáng.</p>
        <ol className="help-steps">
          <li><strong>Chọn vị trí thoải mái</strong><p>Để khuôn mặt, phần thân trên và hai tay nằm trong khung hình. Tránh ánh sáng chiếu từ phía sau.</p></li>
          {recognitionEnabled ? <><li><strong>Nhận diện một ký hiệu</strong><p>Nhấn Nhận diện để ghi một đoạn camera ngắn, thực hiện ký hiệu rồi nhấn Kết thúc. Camera không tự ghi khi vừa bật.</p></li><li><strong>Chủ động gửi hoặc hủy</strong><p>Chọn Gửi nhận diện để phân tích. Bạn có thể hủy đoạn quay hoặc yêu cầu đang xử lý; thử lại nếu kết quả chưa rõ.</p></li></> : recordingEnabled ? <><li><strong>Thực hiện một ký hiệu</strong><p>Nhấn bắt đầu quay, thực hiện trọn ký hiệu rồi nhấn dừng. Bạn có thể hủy bất cứ lúc nào.</p></li><li><strong>Quay lại khi cần</strong><p>Nếu động tác chưa rõ, chọn quay lại để bắt đầu một lượt mới.</p></li></> : <><li><strong>Bật camera khi sẵn sàng</strong><p>Cho phép camera trong trình duyệt. Hình ảnh xem trước giúp bạn điều chỉnh vị trí và ánh sáng.</p></li><li><strong>Tắt camera khi xong</strong><p>Nhấn biểu tượng đặt lại cạnh trạng thái camera để kết thúc xem trước.</p></li></>}
        </ol>
        <div className="help-privacy"><UiIcon name="shield" /><div><strong>Camera do bạn kiểm soát</strong><p>{recognitionEnabled ? 'Không ghi âm. Đoạn camera chỉ được gửi khi bạn chọn Gửi nhận diện, để xử lý tạm thời theo contract của dịch vụ. Hủy yêu cầu ở trình duyệt không đảm bảo dừng ngay việc xử lý phía máy chủ; dịch vụ phải xóa clip sau xử lý.' : recordingEnabled ? 'Ứng dụng không ghi âm. Đoạn quay chỉ ở trong bộ nhớ trang và bị bỏ khi bạn hủy hoặc đóng trang.' : 'Camera hiện chỉ hiển thị hình ảnh xem trước, không tự ghi hình, ghi âm hoặc gửi dữ liệu.'}</p></div></div>
        <p className="help-disclaimer">{vi.disclaimer}</p>
        <button className="primary-button dialog-done" onClick={() => dialog.current?.close()}>Đã hiểu<UiIcon name="check" /></button>
      </dialog>
    </>
  );
}
