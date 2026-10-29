# P5 — Hiển: frontend implementation and handoff

Updated: 2026-10-29. Scope follows `D:/Downloads/ViSign-5HVT-plan.zip`, updated
2026-10-24. The original plan and older review package remain in the source
workspace; this frontend handoff includes the relevant API contract and task evidence.

## Task status

The following tasks are implemented and verified at the frontend boundary. Joint
acceptance with the real backend/model remains a separate handoff checkpoint.

| Task | Status | Implementation / evidence |
|---|---|---|
| T027 | Implemented | `apps/web/src/types/inference-api.ts`; nullable fields, extractor/schema, correlation and optional diagnostics |
| T028 | Implemented | `apps/web/src/content/vi.ts`, Vietnamese views/help/disclaimer and accessible action names |
| T031 | Implemented | `recognition-flow.test.tsx`, `recognition-errors.test.tsx`, `result.test.tsx`; no accepted-result TODO remains |
| T039 | Implemented | `CameraRecorder.tsx`; permission, preview, explicit capture/end/cancel, safety cap, cleanup and stale-event guards |
| T040 | Implemented | `services/inferenceApi.ts`; model-info, camera multipart, X-Request-ID, timeout/abort and response guards; MSW transport tests |
| T041 | Implemented | `useRecognition.ts` attempt reducer and model state, composed with camera permission/recording resource state |
| T042 | Implemented | `RecognitionResult.tsx`, `ModelNotice.tsx`; Vietnamese text/confidence/disclaimer and fixture/pilot/full scope notices |
| T043 | Implemented | `App.tsx` connects the real client, model-info, camera and predictions; same endpoint for all artifact kinds; browser contract fixtures |
| T046 | Implemented | Permission denied, cancel/retry/rejected, busy/unready/decode/network/error cases in `recognition-errors.test.tsx` |
| T051 | Implemented | Rejected results show exact “Không nhận diện được”; suggested text is hidden; retry requires a new capture |
| T052 | Implemented | `RecognitionError.tsx` + camera error catalog; stable Vietnamese messages, raw server text never rendered |
| T053 | Implemented | Timeout, abort, reset/unmount, no duplicate upload, stale response suppression, dropping retained clips and resetting camera |
| T063 — M1 | Additional audit implemented at user's request | Playwright + axe across idle/help/accepted/rejected/error and mobile; modal Tab/Escape/restore, result/error/action focus, camera labels |

T063 remains classified M1 in the supplied plan; this additional audit does not
change the MVP commitment or claim full WCAG conformance. Automatic API type
generation and other M1/M2 candidates were not introduced.

## User-directed UI decisions

- Light neutral background; no person illustration or decorative green wash.
- No numbered toolbar, technical footer or “Bắt đầu quay” button.
- **Bật camera** only starts preview. **Nhận diện → Kết thúc → Gửi nhận diện**
  makes capture/submission explicit and retains the camera-clip API contract.
- Reset sits beside camera status; help/privacy is a keyboard-accessible dialog.
- There is no continuous recognition, automatic recording/upload or file picker.

## Validation

From `apps/web/`:

```powershell
npm test
npm run typecheck
npm run lint
npm run build
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm run test:browser
```

The current verification suite contains 52 Vitest tests and 4 browser tests.
Browser fixtures use actual MediaRecorder WebM from a fake camera, then explicitly
intercept API calls. They check accepted/rejected/busy/unavailable flows and real
multipart bytes, with screenshots for desktop/mobile. Axe scans and keyboard
checks are part of the browser suite; contrast and modal Tab behavior found during
the audit were repaired.

## Handoff / external acceptance

**Tín:** serve the three endpoints in `contracts/openapi.yaml` on port 8000, or
provide `VITE_API_BASE_URL`. Verify CORS/correlation headers if using another
origin. Exercise fixture → pilot → full without changing endpoint shapes. Align
`VITE_MAX_CAPTURE_MS` with server clip limits. Backend owns upload validation,
temporary-file cleanup, concurrency and actual predictor integration.

**Cường:** provide the compatible artifact with correct extractor/schema version,
supported meanings, modelVersion and measured quality metadata. Frontend rejects
results whose modelVersion differs from the loaded model-info until scope refresh.

**Huy:** review UX/copy, physical webcam behavior and shared fixture/API E2E on the
demo laptop. Measure real end-to-end latency and approve release readiness only
after model/data/privacy gates pass.

There is no FastAPI service or trained model in this checkout. Therefore real
backend/model inference, server cleanup, model accuracy/recall and demo latency
are **not verified by the frontend fixtures**. No backend/model task or release
gate has been marked complete by this handoff.
