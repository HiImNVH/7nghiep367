# Backend HTTP status contract note

Owner: P2 Tín
Consumers: P5 Hiển and integration tests
Status: Proposed follow-up, not implemented by this note

## Decision

The API keeps the canonical routes without a trailing slash:

- `GET /api/v1/health`
- `GET /api/v1/model-info`
- `POST /api/v1/predictions`

`404` and `405` must use the same JSON error envelope and correlation rules as
the prediction API. The existing automatic `307` redirect remains the canonical
trailing-slash behavior. `403` and `304` are reserved follow-ups and must not be
claimed as implemented yet.

## Required now

### 404 Route not found

Return this response for an unknown API route:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json
X-Request-ID: <uuid>
```

```json
{
  "code": "ROUTE_NOT_FOUND",
  "message": "Không tìm thấy tài nguyên API.",
  "requestId": "<same uuid as X-Request-ID>"
}
```

Do not expose framework internals, filesystem paths or the unmatched raw URL in
the public message.

### 405 Method not allowed

Return this response when the route exists but the HTTP method is unsupported:

```http
HTTP/1.1 405 Method Not Allowed
Content-Type: application/json
Allow: <methods supplied by the router>
X-Request-ID: <uuid>
```

```json
{
  "code": "METHOD_NOT_ALLOWED",
  "message": "Phương thức HTTP không được hỗ trợ cho tài nguyên này.",
  "requestId": "<same uuid as X-Request-ID>"
}
```

The custom handler must preserve the framework-generated `Allow` header.

### 307 Canonical path redirect

Keep FastAPI/Starlette's existing `307 Temporary Redirect` when a caller adds a
trailing slash, for example:

```text
/api/v1/health/ -> /api/v1/health
```

Requirements:

- Preserve the HTTP method and request body.
- Return the canonical URL in `Location`.
- Include `X-Request-ID`.
- Do not replace this with `302`, because `302` may cause clients to change a
  non-GET request into `GET`.
- Frontend code must call canonical URLs directly and must not depend on the
  redirect.

## Reserved, not required for the current MVP

### 403 Forbidden

Do not add a synthetic `403` response while the MVP has no authentication or
authorization policy. Reserve this contract for a future protected resource:

```json
{
  "code": "FORBIDDEN",
  "message": "Bạn không có quyền thực hiện thao tác này.",
  "requestId": "<uuid>"
}
```

Browser camera permission denial is a frontend/device error and must not be
mapped to this server status. A disallowed CORS preflight currently returns
`400`; it is not a `403` authorization response.

### 304 Not modified

Do not add `304` to health. Health must always report current readiness and
should use `Cache-Control: no-store`.

`304` may be added later to `GET /api/v1/model-info` only when Backend defines an
`ETag`, returns it on `200`, evaluates `If-None-Match`, and documents cache
invalidation after an artifact switch. A `304` response has no JSON body.

## Backend implementation checklist

- [ ] Add `ROUTE_NOT_FOUND` and `METHOD_NOT_ALLOWED` to the stable error catalog.
- [ ] Add framework exception handlers for `404` and `405` in `main.py`.
- [ ] Preserve `Allow` on `405`, `Location` on `307`, and `X-Request-ID` on all responses.
- [ ] Document `404`, `405` and `307` in `contracts/openapi.yaml` where OpenAPI permits.
- [ ] Add contract tests with redirect following disabled.
- [ ] Confirm unknown paths never return the default `{"detail": ...}` shape.
- [ ] Confirm health and model-info canonical paths remain `200` in fixture mode.

## Required contract tests

| Case | Expected |
|---|---|
| `GET /api/v1/not-found` | `404`, `ROUTE_NOT_FOUND`, matching request IDs |
| `POST /api/v1/health` | `405`, `METHOD_NOT_ALLOWED`, `Allow: GET` |
| `GET /api/v1/health/` with redirects disabled | `307`, canonical `Location` |
| `GET /api/v1/health` with `If-None-Match: *` | `200` until caching is deliberately implemented |
| Disallowed CORS origin | Current CORS rejection behavior; do not label it authorization `403` |
