# Frontend HTTP status placeholders

Owner: P5 Hiển
Backend contract: `docs/team/backend-http-status-contract.md`
Status: Placeholder specification, not implemented by this note

## Purpose

Add stable frontend handling for API routing and compatibility failures without
displaying raw backend messages. These placeholders are separate from camera
permission errors and model prediction errors.

## Status mapping

| HTTP result | Frontend key | Vietnamese placeholder | Retry behavior |
|---|---|---|---|
| `404` | `apiRouteNotFound` | `Không tìm thấy chức năng API. Vui lòng kiểm tra phiên bản dịch vụ.` | Do not retry automatically |
| `405` | `apiMethodNotAllowed` | `Ứng dụng và dịch vụ chưa tương thích. Vui lòng tải lại trang.` | One user-triggered reload or retry only |
| `307` | No visible error | Follow redirect automatically, but fix the client URL to the canonical path | No UI action |
| `403` future | `apiForbidden` | `Bạn không có quyền thực hiện thao tác này.` | Do not retry automatically |
| `304` future | No visible error | Reuse the cached model information | No UI action |
| CORS/network failure | Existing connection error | Keep the current connectivity guidance | User-triggered retry |

The UI must not show raw `detail`, `message`, HTML, proxy text or stack traces
received from the server.

## Client rules

- Keep the three canonical URLs without a trailing slash.
- Continue to send `X-Request-ID` and read the echoed value.
- Treat `404` and `405` as integration/version mismatches, not as recognition
  failures and not as low-confidence results.
- Do not map browser camera permission denial to server `403`.
- Do not add special `302` handling. Backend has selected `307` so methods and
  bodies are preserved.
- A fetch client may follow `307` automatically, but tests must verify that the
  source URL is already canonical so prediction uploads are not redirected in
  normal operation.
- Do not implement model-info caching until Backend publishes the `ETag` and
  invalidation contract. Until then, a conditional model-info request returning
  `200` is correct.

## Suggested placeholders in code

Add keys to the Vietnamese error catalog rather than embedding text in the API
client:

```ts
apiRouteNotFound: 'Không tìm thấy chức năng API. Vui lòng kiểm tra phiên bản dịch vụ.',
apiMethodNotAllowed: 'Ứng dụng và dịch vụ chưa tương thích. Vui lòng tải lại trang.',
apiForbidden: 'Bạn không có quyền thực hiện thao tác này.',
```

The API client should classify the status into a typed application error. The
view should select copy from `content/vi.ts` and retain the existing accessible
`role="alert"` and focus behavior.

## Frontend implementation checklist

- [ ] Add the three Vietnamese placeholder keys to `apps/web/src/content/vi.ts`.
- [ ] Add typed `404` and `405` classifications in `apps/web/src/services/inferenceApi.ts`.
- [ ] Reserve the `403` key without presenting it as a currently reachable MVP state.
- [ ] Ensure every API constant uses a canonical path without a trailing slash.
- [ ] Keep `307` invisible to users and prevent normal prediction uploads from redirecting.
- [ ] Add component tests for `404` and `405` using stable Vietnamese copy.
- [ ] Add a transport test confirming raw backend messages are never rendered.
- [ ] Add future `304` coverage only after Backend implements the ETag contract.

## Acceptance cases

| Case | Expected UI |
|---|---|
| Model-info returns `404` | Integration/version message; no camera submission |
| Prediction returns `404` | Integration/version message; captured clip cleared safely |
| Prediction returns `405` | Compatibility message; no automatic resubmission |
| Canonical request receives `200` | Existing recognition flow unchanged |
| Unexpected raw server text | Text is not rendered; stable Vietnamese copy is used |
| Camera permission denied | Existing camera-permission message, never `apiForbidden` |
