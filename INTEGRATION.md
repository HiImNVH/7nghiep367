# Chạy bản tích hợp local
Tại thư mục này mở hai PowerShell, mỗi cửa sổ chạy một dòng:
~~~powershell
.\.int-env\Scripts\python.exe -m uvicorn visign_api.main:app --host 127.0.0.1 --port 8000
npm.cmd --prefix apps/web run dev -- --port 5173 --strictPort
~~~
Mở http://127.0.0.1:5173 và http://127.0.0.1:5173/api/v1/model-info. Fixture trả kết quả cố định để thử giao tiếp; không dùng để đánh giá nhận diện.

Data: Inspect-Data.ps1 đọc Data tại vị trí gốc và ghi .local/inventory-generated.csv. Sao chép file này trước khi rà soát vì mỗi lần chạy sẽ tạo lại. Tùy chọn -Clip nhận đường dẫn tương đối bên trong Data để xuất tọa độ, ảnh và tensor với bộ xử lý ở Demo 2. Ví dụ:
~~~powershell
.\Inspect-Data.ps1 -Clip '1. Giấy tờ (giấy)\HCM_Giấy_1.mp4'
~~~
Trước pilot: xác minh nguồn và quyền sử dụng từng clip, duyệt nghĩa/biến thể, signerId và split không trùng người; rà hai thư mục Cảm ơn. Duyệt phiên bản schema và extractor chung với backend. Huấn luyện pilot tối đa 3 nghĩa rồi bàn giao trọng số, model_info và bộ dự đoán GRU; kiểm tra cùng clip tạo cùng tensor khi train và serve. Pilot giữ demoReady=false. Chỉ sau đó mở rộng 10 nghĩa, đánh giá trên người ký giữ riêng, báo accuracy, precision/recall từng nghĩa, Macro-F1, confusion matrix và latency; chỉ phát hành khi đạt đầy đủ gate của lead.
