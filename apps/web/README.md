# ViSign frontend

React + TypeScript + Vite, targeting Chromium/Edge. This implements Hiển's frontend
MVP tasks from the plan ZIP updated 2026-10-24. Status/evidence is recorded in
`../../docs/team/frontend.md`.

## Run

Node.js 22.12+ and npm:

```powershell
cd D:\Projects\7nghiep367\apps\web
npm ci
npm run dev
```

Open the URL printed by Vite. Requests to `/api` use Vite's local proxy to
`http://127.0.0.1:8000`. Run Tín's compatible inference API there. To use another
origin, copy `.env.example` to `.env.local` and set `VITE_API_BASE_URL`; restart
Vite after changing environment values. Direct cross-origin access requires the
API to allow the frontend origin and `X-Request-ID`, and expose `X-Request-ID` and
`Retry-After` response headers. Production hosting needs a same-origin `/api`
reverse proxy or the configured API origin; Vite's development proxy is not a
production server.

There is **no production mock/fallback predictor**. If the API is missing, the UI
shows a recoverable service error. Test fixtures exist only under `tests/`.

## Camera workflow

The user-requested light theme remains. There is no person illustration, numbered
four-button bar, technical footer, or button labelled **Bắt đầu quay**.

1. **Bật camera** requests permission and starts a mirrored preview without audio.
   It does not record or upload anything.
2. **Nhận diện** explicitly records one short isolated sign. **Kết thúc** ends it;
   a configurable safety cap also ends long captures, without uploading them.
3. **Gửi nhận diện** explicitly uploads the clip as multipart `clip`. The user can
   discard the clip before sending, or cancel an in-flight request.
4. Results show Vietnamese text/confidence or **Không nhận diện được**. Retry
   requires a fresh capture; reset stops tracks, aborts requests and drops clips.

`VITE_MAX_CAPTURE_MS` defaults to 5000 (accepted range 1000–30000); invalid values
fall back to 5000. It must be aligned with the backend's actual duration limits.
`VITE_API_TIMEOUT_MS` defaults to 10000; it is a network timeout, not evidence of
meeting the model's 3-second p95 performance target. Cancelling a browser request
does not guarantee immediate cancellation of server work; backend cleanup remains
mandatory.

## Modules and contract

- `src/types/inference-api.ts`: minimal manual wire types from
  `../../contracts/openapi.yaml` (exact copy from the updated plan ZIP).
- `src/services/inferenceApi.ts`: runtime shape checks, UUID correlation,
  multipart submission, stable error catalog, optional diagnostics, timeout/abort.
- `useRecognition.ts`: model scope and attempt reducer, request ownership and
  generation guards; late responses cannot replace reset/newer attempts.
- `CameraRecorder.tsx`: owns camera/recorder resources, permission and clip capture;
  composes the recognition controller. Its standalone default remains preview
  only; `recordingEnabled` opts into the manual test/reusable mode. The real App
  supplies the recognition controller and the explicit Nhận diện workflow.
- `RecognitionResult`, `RecognitionError`, `ModelNotice`: server acceptance,
  Vietnamese feedback, fixture/pilot/full disclosure and actual supported meanings.

Fixture/pilot always show limited/test mode, even if metadata contradicts that.
Full readiness also checks the published vocabulary count and quality metadata.
Diagnostics do not determine acceptance. An artifact version change between
model-info and prediction forces a scope refresh instead of attributing the result
to stale metadata. Nullable fixture metrics are shown as unevaluated, never zero.

Camera clips, frames and landmarks are not written to storage or console logs.
Only camera capture is offered; there is no file-upload input. Clips are released
from state/refs on submit/cancel/reset/unmount. Header IDs stay available for
support while raw server messages are never rendered.

## Verification

```powershell
npm test
npm run typecheck
npm run lint
npm run build
npx playwright install chromium
npm run test:browser
```

On Windows with Edge already installed:

```powershell
$env:VISIGN_BROWSER_CHANNEL = 'msedge'
npm run test:browser
```

- Vitest/RTL tests cover permission, recording lifecycle, accepted/rejected results,
  service errors, retries, timeout/cancel/reset and late-response races.
- MSW tests exercise real fetch multipart/correlation handling against the API
  contract, without starting a backend.
- Browser tests use a real MediaRecorder with Chromium's fake camera and explicitly
  intercepted API responses. They assert a real WebM EBML header in the upload.
- Axe checks run on idle/help/accepted/rejected/error views, including mobile;
  keyboard tests cover modal focus containment, Escape and focus restoration.
  These checks are not a claim of complete WCAG conformance.

Frontend checks do not establish physical-camera compatibility, actual API cleanup,
model quality, real inference latency or permission to release a demo. Those need
joint acceptance with Tín/Cường/Huy on the demo laptop.
