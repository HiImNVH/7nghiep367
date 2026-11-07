# ViSign implementation tracking snapshot

Snapshot date: 2026-11-07
Source of truth: `specs/001-vsl-recognition-mvp/tasks.md`
Scope: Review of remote role branches before application code is merged into `main`

## Status rules

- `MAIN`: implementation and required evidence are merged into `main`.
- `BRANCH`: implementation evidence exists on a remote role branch but is not yet
  release-complete on `main`.
- `PARTIAL`: code or tests exist, but required real data, artifact or acceptance
  evidence is missing.
- `TODO`: no sufficient implementation evidence was found.

Only `tasks.md` owns task checkboxes. This snapshot records integration readiness
and must be refreshed after each role branch is merged.

## Repository baseline

| Area | Branch reviewed | Commit | Assessment |
|---|---|---|---|
| Main requirements and tasks | `main` | This Spec Kit bootstrap commit | Requirements, plans, contracts and backlog installed |
| Frontend | `frontend` | `c6a1b45` | Code and automated frontend tests exist |
| Backend | `backend` | `b708c72` | API, GRU artifact adapter and read-only handoff checker exist; supplied backend report says 119 tests passed |
| Integrated frontend/backend | `integration` | `7f3ae0d` | Integration branch exists, not merged into main |
| AI and model integration | `Model/Cường` | `985e871` | Training/evaluation pipeline exists; no approved VSL model |
| Internal admin/train tool | `admin/train-model` | `73825c7` | Clip inspection, pilot job UI/API and W&B history code exist; not merged or accepted |
| Data | `data` | `bcc97ca` | Contains a video archive only; no approved manifests or split evidence |

## Member status

| Person | Owner | Tasks | Status | Evidence and next gate |
|---|---|---|---|---|
| P1 | Huy | T032, T047, T067–T071, T084 | PARTIAL | Browser fixture tests exist. Full browser→API→model E2E, verification/demo/usability reports and admin scope acceptance remain open. |
| P2 | Tín | Backend/API tasks plus T072–T073, T078–T080 | BRANCH / TODO | Backend report maps 14/16 backend requirements as implemented at `b708c72`; 404/405/no-store work and admin contract/security tests remain. Merge and rerun on main. |
| P3 | Cường | AI/training/evaluation tasks plus T083 support | PARTIAL | Pipeline and training tools exist; pilot Sốt-Chờ was reported at Macro-F1 0.333 and is not release evidence. Full 10-meaning model and gate evidence remain. |
| P4 | Quang | T008–T013, T018, T056, T061, T076–T077 | PARTIAL / TODO | Supplied current-state document reports 42 development clips and a 6-clip Sốt-Chờ pilot. Official full manifest/coverage/signer split evidence remains open. |
| P5 | Hiển | Frontend tasks plus T063, T074–T075, T081–T082 | BRANCH / TODO | Recognition UI/tests and admin UI exist on branches. HTTP placeholders, admin tests/client cleanup and real webcam acceptance remain. |

## Verified test evidence before main integration

- Python: 167 passed, 8 skipped because reviewed WebM clips and a trained artifact were not supplied.
- Frontend unit/component tests: 55 passed.
- Playwright browser tests: 6 passed using a fake camera and mocked API responses.
- ESLint, TypeScript production build, Ruff and basic mypy checks passed.

These results show branch readiness, not release completion. Browser tests that
mock API responses do not replace full application E2E acceptance.

Additional supplied evidence dated 2026-11-06/07 has not yet been reproduced on `main`: backend
119-test claim, frontend handoff 52 unit/component + 4 browser tests, pilot model
`vsl-pilot-d69ea4eb994f`, and W&B run evidence. These remain `BRANCH/PARTIAL` until merged and rerun.

## Immediate integration order

1. Finish T072–T075 and merge backend/frontend foundation in reviewable PRs with task IDs.
2. Merge AI shared pipeline after schema v0.3 and train-serving parity review.
3. Complete T076 pilot audit; keep reported Sốt-Chờ result explicitly non-release.
4. Complete T077 full manifest and signer-held-out split; then train/evaluate full 10 meanings.
5. Review/harden admin tool through T078–T084 without coupling it to public `/api/v1`.
6. Run quickstart/E2E/latency/usability on `main`; only then close tasks and approve demo.
