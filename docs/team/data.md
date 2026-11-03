# Data Work Dashboard

Cross-team integration snapshot: [implementation-status.md](implementation-status.md).

Statuses below are role/historical evidence. Release completion is controlled by
the checkbox in `specs/001-vsl-recognition-mvp/tasks.md` after merge to `main`.

| Field | Value |
|---|---|
| Worker ID | `P4` |
| Role ID | `data` |
| Current member | Quang |
| Scope | Source/license audit, label review, pilot/full manifests, coverage and leakage-free splits |
| Last updated | 2026-10-22 |

## Current Progress

| Task | Status | Next action / Blocker | Evidence |
|---|---|---|---|
| T008 | DONE | Raw-material and licensing guidance completed | `data/README.md` |
| T009 | DONE | Meaning/SignClass entities completed | `ai/src/visign_ai/dataset/entities.py` |
| T010 | DONE | Manifest row schema completed | `ai/src/visign_ai/dataset/manifest_schema.py` |
| T011 | DONE | Manifest validation tests completed | `ai/tests/dataset/test_manifest_validation.py` |
| T012 | DONE | Manifest validator completed | `ai/src/visign_ai/dataset/validate_manifest.py` |
| T013 | DOING | Audit source/license per video, then deliver approved `pilot.csv` | `data/manifests/p0-meanings.csv` |
| T018 | TODO | Create leakage-free split after pilot/full manifest handoff | — |
| T056 | TODO | Add split leakage regression tests | — |
| T061 | TODO | Generate dataset card from final manifest audit | — |

## T013 Milestones

| Milestone | Status | Deliverable |
|---|---|---|
| D0 P0 vocabulary freeze | DONE | `data/manifests/p0-meanings.csv`, exactly 10 meanings |
| D1 Source/license inventory | DOING | Audited source list |
| D2 Pilot subset | TODO | `data/manifests/pilot.csv`, at most 3 approved meanings |
| D3 Full coverage | TODO | Coverage report for 10 P0 meanings |
| D4 Sample manifest freeze | TODO | `data/manifests/p0.csv` covering exactly 10 meanings |
| D5 Data checkpoint | TODO | Huy approval and Cường handoff |

## Checkpoint Responsibilities

- Never admit samples with unknown license or rejected verification status.
- Keep signer/session identifiers anonymous and splits leakage-free.
- Keep the frozen meaning IDs stable; any rename requires a reviewed registry change before training.

## Handoff Notes

- Current risks: The vocabulary is frozen, but raw material coverage and usage rights are not yet approved.
- Required reviewers: Huy for checkpoint; Cường as manifest consumer.
- Work-in-progress limit: T013 is the only active data task until pilot handoff.

## Handoff History

| Date | From | To | Open work and evidence |
|---|---|---|---|
| 2026-10-22 | — | Quang | Initial assignment; T008–T012 done, T013 active |
| 2026-10-22 | Quang | Huy, Cường | P0 vocabulary frozen; sample/license audit remains open in T013 |
