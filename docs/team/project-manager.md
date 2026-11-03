# Project Manager Work Dashboard

Cross-team integration snapshot: [implementation-status.md](implementation-status.md).

Statuses below are role/historical evidence. Release completion is controlled by
the checkbox in `specs/001-vsl-recognition-mvp/tasks.md` after merge to `main`.

| Field | Value |
|---|---|
| Worker ID | `P1` |
| Role ID | `project-manager` |
| Current member | Huy |
| Scope | Scope, backlog, dependency, checkpoint, E2E, verification and demo acceptance |
| Last updated | 2026-10-22 |

## Current Progress

| Task | Status | Next action / Blocker | Evidence |
|---|---|---|---|
| T032 | TODO | Chờ fixture contract; chuẩn bị synthetic-camera happy path | — |
| T047 | TODO | Chờ error contract; chuẩn bị negative E2E matrix | — |
| T067 | TODO | Chạy quickstart sau khi các track tích hợp hoàn tất | — |
| T068 | TODO | Soạn kịch bản full và pilot giới hạn | — |
| T070 | TODO | Tổng duyệt trên laptop đích với artifact metadata | — |
| T069 | TODO | Tổng hợp README từ hướng dẫn của các vai trò | — |
| T071 | TODO | Lập kế hoạch usability test ít nhất 10 người | — |

## Checkpoint Responsibilities

- Duyệt fixture để mở FE/BE/E2E; không xem fixture là bằng chứng model quality.
- Duyệt pilot chỉ cho smoke integration và xác nhận `demoReady=false`.
- Duyệt data checkpoint sau khi Quang đóng băng `p0.csv` và split audit sạch.
- Chỉ duyệt full model khi Cường cung cấp gate report và Tín xác nhận API smoke tests.

## Handoff Notes

- Current risks: T013 phụ thuộc raw material; full training có thể trễ.
- Required reviewers: `backend-api`, `training-models`, `data`, `frontend` theo checkpoint.
- Work-in-progress limit: Maximum 2 tasks in `DOING`.

## Handoff History

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-10-22 | — | Huy | Initial assignment; 7 open tasks |
