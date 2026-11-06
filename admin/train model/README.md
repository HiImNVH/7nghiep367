# ViSign Admin

## Mở bằng hai terminal trong VS Code

Mở thư mục gốc `7nghiep367` bằng **File → Open Folder** và kiểm tra đang ở nhánh `admin/train-model`. Chọn **Terminal → New Terminal**, dùng profile **PowerShell**. Sau khi chạy backend, bấm **+** ở bảng Terminal để mở terminal thứ hai cho frontend.

### Terminal 1 — Backend

Máy hiện tại đã có `.venv-ai`, detector và W&B. Máy mới cài môi trường theo [README AI](../../ai/README.md), cài thêm W&B bằng `python -m pip install -e './ai[tracking]'` trong môi trường đó. Nếu môi trường do uv quản lý và thiếu pip, dùng `uv pip install --python .\.venv-ai\Scripts\python.exe -e './ai[tracking]'`.

Từ gốc repo, chạy các lệnh bên dưới. Đổi đường dẫn nếu thư mục bàn giao đã giải nén nằm chỗ khác. Backend đọc thư mục chứa data/manifests hoặc ZIP gốc.

```powershell
$env:VISIGN_PILOT_DATA = 'K:\Dự án ViSign\ViSign-nháp-2'
$env:WANDB_PROJECT = 'visign-pilot'
$env:WANDB_MODE = 'offline'
$env:VISIGN_ADMIN_TOKEN = Read-Host 'Đặt mã admin'
.\.venv-ai\Scripts\python.exe -m uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2 — Frontend

Mở terminal PowerShell mới tại gốc repo. Sao chép cả khối lệnh để npm chạy trong apps/web. Nếu trang Admin đang mở được, dùng phiên hiện tại.

```powershell
Set-Location apps/web
if (-not (Test-Path node_modules)) { npm.cmd ci }
npm.cmd run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Giữ hai terminal mở. Vào [ViSign](http://127.0.0.1:5173/) rồi bấm **Admin** ở góc phải. Nếu trang đang chạy, chỉ cần tải lại. Nếu gặp `WinError 10048` hoặc cổng đã được dùng, dừng đúng phiên ViSign cũ bằng **Ctrl+C** trong terminal đang chạy phiên đó rồi chạy lại. Nếu terminal hỏi `Terminate batch job (Y/N)?`, nhập **Y**. Nếu phiên cũ chạy nền, xem PID bằng `Get-NetTCPConnection -LocalPort 8000,5173 -State Listen` và xác nhận đó là ViSign trước khi dừng. Nếu hộp thoại báo API pilot chưa sẵn sàng, kiểm tra terminal backend đang chạy từ đúng repo và nhánh.

## Kiểm tra clip và chạy pilot

- **Kiểm tra clip:** Chọn MP4/WebM → **Chạy kiểm tra** → nhập mã admin. Có thể mở lại thư mục kết quả cũ hoặc tải ZIP ảnh, CSV và NPZ. Công cụ xem clip dùng Demo 2 v0.2.
- **Train thử:** Vào **Huấn luyện pilot → Kiểm tra dữ liệu**. Khi đủ 6/6 clip qua pipeline v0.3, bấm **Bắt đầu train thử**. Hộp thoại hiện epoch, điểm test và trạng thái W&B. Có thể đóng rồi mở lại để xem tiến độ.
- Kết quả mỗi job lưu ở `.local/pilot-runs/<mã-job>/evaluated`. Mở `evaluation-report.json` để xem điểm, `confusion-matrix.png` để xem nhầm lẫn và `training-report.json` để xem loss. Pilot có hai clip test. CPU là mặc định, có thể đặt `VISIGN_PILOT_DEVICE=cuda` nếu môi trường đã hỗ trợ.

## Xem biểu đồ trên web W&B

Nếu hộp thoại có nút **Mở biểu đồ W&B**, bấm vào rồi xem **Workspace**. Nếu ghi **Đã ghi log cục bộ**, đồng bộ sau khi job hoàn tất. Không cần train lại. Dùng **terminal PowerShell thứ ba** trong VS Code tại gốc repo. Lấy API key ở [trang đăng nhập W&B](https://wandb.ai/authorize) và dán khi lệnh `login` hỏi.

Ví dụ cho job trong ảnh, mã `d69ea4eb994f`, run `jo7g41ay`. Với job khác, dùng mã trong hộp thoại hoặc mở mục **Cách mở run trên web W&B** để lấy lệnh tương ứng.

```powershell
.\.venv-ai\Scripts\wandb.exe login
$run = Get-ChildItem '.local/pilot-runs/d69ea4eb994f/wandb' -Directory -Filter 'offline-run-*-jo7g41ay'
.\.venv-ai\Scripts\wandb.exe sync --project visign-pilot $run.FullName
```

Nếu cần đồng bộ vào team, thêm `--entity ten-team` vào lệnh sync. Mở URL in trong terminal hoặc vào project **visign-pilot**, chọn run theo mã và xem **Workspace**. Tìm `train_loss` và `validation_loss` theo epoch. Mục **Overview** có cấu hình và chỉ số tổng hợp. [Tham khảo lệnh W&B sync](https://github.com/wandb/wandb/blob/main/wandb/cli/cli.py)

Muốn có link ngay trong lần train sau, đăng nhập W&B một lần bằng wandb login rồi chạy backend online như hướng dẫn bên dưới.

## Dùng webcam với model đã train

Sau khi pilot hoàn tất, mở **Admin → Lịch sử train** để lấy mã job. Dừng backend cũ rồi chạy trong terminal PowerShell của VS Code tại gốc repo:

~~~powershell
& '.\admin\train model\Start-PilotWebcam.ps1' -JobId d69ea4eb994f -PilotData 'K:\Dự án ViSign\ViSign-nháp-2'
~~~

Giữ frontend chạy và tải lại trang nhận diện. Kiểm tra /api/v1/model-info trả artifactKind là pilot và modelVersion mang mã job đã chọn. Bật camera, thực hiện một ký hiệu mỗi clip, rồi so kết quả với ký hiệu vừa làm. Script kiểm tra SHA-256 checkpoint và dùng schema của chính job. Lần train mới không tự thay checkpoint đang phục vụ.

## Kết nối W&B online cho lần train sau

Mã admin chỉ mở công cụ ViSign. API key W&B cho phép backend gửi log vào tài khoản W&B. Nếu máy chưa đăng nhập, lấy key tại https://wandb.ai/authorize và chạy wandb login một lần. Backend dùng thông tin đăng nhập đã lưu. Nếu đã đăng nhập, chạy từ dòng đặt WANDB_PROJECT:

~~~powershell
.\.venv-ai\Scripts\wandb.exe login
$env:WANDB_PROJECT = 'visign-pilot'
# Nếu ghi vào nhóm, đặt WANDB_ENTITY bằng slug team có quyền ghi.
& '.\admin\train model\Start-PilotWebcam.ps1' -JobId d69ea4eb994f -PilotData 'K:\Dự án ViSign\ViSign-nháp-2' -WandbMode online
~~~

Nếu dùng lệnh Uvicorn thông thường ở đầu README, đặt WANDB_MODE=online trong cùng terminal. Sau khi bắt đầu một job mới, mục **Lịch sử train** cập nhật theo tiến độ và có link W&B khi SDK tạo run online. Run offline dùng lệnh sync riêng ở mục trên. Sau sync, dùng URL CLI trả về vì lịch sử ViSign vẫn ghi lại chế độ lúc train. Run ghi loss, cấu hình và điểm đánh giá. Video thô nằm trong dữ liệu cục bộ.
