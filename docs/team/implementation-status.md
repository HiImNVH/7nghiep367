# ViSign implementation tracking snapshot

Snapshot date: 2026-11-03
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
| Backend | `backend` | `a1217f8` | API code and contract tests exist |
| Integrated frontend/backend | `integration` | `7f3ae0d` | Integration branch exists, not merged into main |
| AI and model integration | `Model/Cường` | `985e871` | Training/evaluation pipeline exists; no approved VSL model |
| Data | `data` | `bcc97ca` | Contains a video archive only; no approved manifests or split evidence |

## Member status

| Person | Owner | Tasks | Status | Evidence and next gate |
|---|---|---|---|---|
| P1 | Huy | T032, T047, T067–T071 | PARTIAL | Browser fixture tests exist, but full frontend→API→model E2E, verification report, demo rehearsal and usability report remain open. |
| P2 | Tín | T019–T026, T030, T037–T038, T044–T045, T048–T050, T055, T060, T064, T066, T072–T073 | BRANCH / TODO | Backend tests and fixture API exist on role/integration branches. T072–T073 for stable 404/405/307 handling are new TODO items. Merge and rerun tests on main. |
| P3 | Cường | T014–T017, T029, T033–T036, T054, T057–T059, T062, T065 | PARTIAL | Decoder, MediaPipe, GRU, evaluation and artifact tooling exist. Feature schema approval, reviewed browser clips, approved manifest, trained VSL weights and real quality/latency evidence remain missing. |
| P4 | Quang | T008–T013, T018, T056, T061 | TODO / HISTORICAL | Earlier local workspace marked T008–T012 complete, but remote branches do not contain their manifest/schema evidence. Pilot/full manifests, signer-held-out split audit and dataset card remain open. |
| P5 | Hiển | T027–T028, T031, T039–T043, T046, T051–T053, T074–T075; M1 T063 | BRANCH / TODO | Frontend implementation, unit tests, browser tests and accessibility evidence exist on the frontend/model branches. T074–T075 HTTP compatibility placeholders are new TODO items. |

## Verified test evidence before main integration

- Python: 167 passed, 8 skipped because reviewed WebM clips and a trained artifact were not supplied.
- Frontend unit/component tests: 55 passed.
- Playwright browser tests: 6 passed using a fake camera and mocked API responses.
- ESLint, TypeScript production build, Ruff and basic mypy checks passed.

These results show branch readiness, not release completion. Browser tests that
mock API responses do not replace full application E2E acceptance.

## Immediate integration order

1. Merge this Spec Kit/source-of-truth bootstrap into `main`.
2. Reconcile and merge frontend/backend integration code with task IDs in the PR.
3. Merge AI pipeline code after schema and artifact boundaries are reviewed.
4. Produce approved pilot/full manifests and signer-held-out split evidence.
5. Train and evaluate a real pilot artifact, then run unskipped E2E and latency checks.
6. Update this snapshot and mark tasks complete only after evidence is on `main`.
