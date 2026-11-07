# Internal Admin Tool Contract

This contract applies only to the opt-in local `/api/admin/*` tool. It is not part of the public
`/api/v1` recognition contract and must not be exposed without an explicit deployment decision.

## Security boundary

- The API is disabled when `VISIGN_ADMIN_TOKEN` is absent.
- Enabled requests require `Authorization: Bearer <token>`.
- Tokens, W&B keys, raw clips and stack traces must not be committed or returned.
- Inspect artifacts are temporary and are removed after download or failure.

## Endpoints

| Method | Path | Purpose | Required behavior |
|---|---|---|---|
| POST | `/api/admin/inspect` | Inspect one MP4/WebM clip and download a ZIP report | Enforce byte limit and single inspection; cleanup in all paths |
| GET | `/api/admin/pilot` | Read current pilot state | Return a `TrainingRun` state |
| GET | `/api/admin/pilot/history` | Read local run history | Return sanitized run summaries, newest first |
| POST | `/api/admin/pilot/prepare` | Validate handoff and extract pilot features | Return 202; reject when a job is active |
| POST | `/api/admin/pilot/train` | Train/evaluate a prepared pilot | Return 202; require `ready`; reject concurrent job |

## Stable outcomes

- Disabled tool: 404.
- Invalid token: 401.
- Another inspection or training job is active: 409.
- Invalid handoff/clip: 4xx with a stable Vietnamese message.
- Worker unavailable or environment incomplete: 503.
- Inspection timeout: 504.

Pilot metrics are integration evidence only. No admin endpoint may set a pilot artifact to
`demoReady=true` or bypass the full 10-meaning signer-held-out release gate.
