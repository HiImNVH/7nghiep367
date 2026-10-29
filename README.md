# ViSign — Frontend của Hiển (P5)

Phần UX/UI và frontend dùng React, TypeScript và Vite. Mã nguồn nằm trong
`apps/web/`, API contract nằm trong `contracts/`, bảng nhiệm vụ và bằng chứng
kiểm tra nằm trong `docs/team/frontend.md`.

## Chạy frontend

Cài Node.js phiên bản 22.12 trở lên, rồi mở terminal tại thư mục repo:

```powershell
cd apps/web
npm ci
npm run dev
```

Mở địa chỉ Vite in ra trong terminal. Frontend mặc định kết nối backend ở
`http://127.0.0.1:8000` thông qua proxy `/api`. Cần chạy API tương thích của Tín
để nhận diện thật. Nếu backend chưa chạy, giao diện sẽ báo lỗi kết nối và cho
phép thử lại. Bản này không kèm backend hoặc model đã huấn luyện.

Xem `apps/web/README.md` để cấu hình API và tìm hiểu luồng camera.

## Kiểm tra

Chạy tại `apps/web/`:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Kiểm tra trình duyệt trên Windows có Microsoft Edge:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm run test:browser
```

Tests dùng dữ liệu API mô phỏng và camera giả trong môi trường kiểm thử.
Tích hợp backend/model thật và nghiệm thu trên máy demo cần làm cùng nhóm.
