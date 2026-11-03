# ViSign Team Work Tracking

Current cross-team integration assessment:
[implementation-status.md](implementation-status.md). `tasks.md` remains the
only authoritative checkbox backlog.

Thư mục này lưu dashboard tiến độ theo **vai trò ổn định**, không đặt tên file theo tên cá nhân. Khi
thay thành viên, giữ nguyên file vai trò, cập nhật `Current member` và thêm một dòng vào `Handoff
history`. Cách này bảo toàn lịch sử, dependency và bằng chứng công việc.

## Nguồn sự thật

1. `specs/001-vsl-recognition-mvp/tasks.md` là nguồn sự thật cho owner và checkbox hoàn thành.
2. File vai trò trong thư mục này là dashboard cá nhân: trạng thái hiện tại, blocker, next action và
   bằng chứng.
3. Khi hai nơi khác nhau, sửa member file theo `tasks.md`; không tự đổi owner trong dashboard.

## Quy ước mã người

| Mã | Thành viên hiện tại | Vai trò |
|---|---|---|
| `P1` | Huy | Project/Task Manager |
| `P2` | Tín | Backend/API |
| `P3` | Cường | Training Models |
| `P4` | Quang | Data |
| `P5` | Hiển | Frontend |

P1–P5 có nghĩa `Person 1`–`Person 5`, không phải độ ưu tiên. `[P]` trong `tasks.md` vẫn chỉ cho biết
task có thể chạy song song.

## Quy ước mức thay đổi plan

| Mã | Nghĩa | Cách dùng |
|---|---|---|
| `M0` | Bắt buộc để đóng lỗ hổng MVP trước pilot | Đã ánh xạ vào task `T*` hiện hành |
| `M1` | Cải thiện trước full/demo khi trigger và evidence được Huy duyệt | Chưa mặc định là task cam kết |
| `M2` | Sau MVP hoặc chỉ làm khi benchmark/scope mới yêu cầu | Không nằm trên critical path |

Khi ghi owner dùng `Person P1`–`Person P5`; khi ghi mức áp dụng kỹ thuật dùng `M0`–`M2`; khi ghi độ
ưu tiên story dùng `US Priority P1/P2`; khi ghi phạm vi từ dùng `Vocabulary P0`.

Khi trao đổi, dùng `Person P1` hoặc `@P1` cho người thực hiện; dùng `US Priority P1/P2` khi nói về
độ ưu tiên của User Story để tránh nhầm hai hệ mã.

## Quy ước trạng thái

```text
TODO -> DOING -> REVIEW -> DONE
          \-> BLOCKED -> DOING
```

| Status | Khi sử dụng |
|---|---|
| `TODO` | Chưa bắt đầu hoặc dependency chưa mở |
| `DOING` | Đang thực hiện; mỗi người tối đa 2 task DOING |
| `BLOCKED` | Không thể tiếp tục; phải ghi blocker và task/người phụ thuộc |
| `REVIEW` | Đã có đầu ra, đang chờ review/test |
| `DONE` | Đã có bằng chứng và checkbox tương ứng trong `tasks.md` là `[X]` |

## Nhịp cập nhật

- Khi bắt đầu: chuyển một task sang `DOING`, ghi `Next action` cụ thể.
- Khi kết thúc phiên làm việc: cập nhật status, blocker và evidence.
- Khi hoàn thành: thêm test/report/commit/PR hoặc đường dẫn artifact vào `Evidence`, rồi cập nhật
  checkbox trong `tasks.md`.
- Huy rà soát dashboard tại mỗi checkpoint fixture, pilot, data, full-model và demo.

## Bàn giao khi đổi người

1. Không đổi tên file vai trò.
2. Cập nhật `Current member` và `Last updated`.
3. Chuyển mọi `DOING` về `BLOCKED` hoặc `REVIEW` với ghi chú rõ ràng.
4. Thêm dòng vào `Handoff history`: ngày, người cũ, người mới, task đang mở và vị trí evidence.
5. Người mới xác nhận `Next action` trước khi chuyển task về `DOING`.

## Danh mục vai trò

| Worker ID | Role ID | Current member | Dashboard |
|---|---|---|---|
| `P1` | `project-manager` | Huy | [project-manager.md](project-manager.md) |
| `P2` | `backend-api` | Tín | [backend-api.md](backend-api.md) |
| `P3` | `training-models` | Cường | [training-models.md](training-models.md) |
| `P4` | `data` | Quang | [data.md](data.md) |
| `P5` | `frontend` | Hiển | [frontend.md](frontend.md) |

File mới phải bắt đầu từ [member-template.md](member-template.md).
