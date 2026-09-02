# Stage 2B-2 dynamic todo BYOS server

Status: **LOCAL IMPLEMENTATION ONLY**. Stage 2B-1 remains device-verified; this dynamic Supabase path has not yet been deployed or tested on the Nook.

```text
screen_state.main
  → TodoProvider
  → NormalizedContent(type, body, updated_at)
  → 600x800 black/white portrait
  → counterclockwise pre-rotation
  → cached 800x600 PNG
  → short-lived signed image URL
  → TRMNL v0.16.0 clockwise rotation
  → 600x800 Nook portrait
```

The existing GitHub Pages frontend, Supabase Auth/RLS, and Stage 2B-1 calibration image are intentionally unchanged.

## Security model

- The Nook continues to authenticate `GET /api/display` with `ID` and `access-token`.
- The server reads only `screen_state?id=eq.main&select=text,updated_at`.
- A new `sb_secret_...` Supabase server key is sent only in the REST `apikey` header. It is not a JWT and is never sent as a Bearer token.
- The server key and signing secret must exist only as secret Render environment variables. They never appear in URLs, responses, logs, frontend files, or Nook settings.
- The Nook client does not forward API auth headers when fetching `image_url`. Dynamic images therefore use a short-lived HMAC-SHA256 capability URL.
- `/screen/test.png` remains public only as a non-private Stage 2B-1 diagnostic artifact.

Canonical image signature input:

```text
GET
/screen/current.png
v=<20-char version>
exp=<unix-seconds>
```

The signature is URL-safe Base64 without padding and is verified with `hmac.compare_digest`.

## Environment variables

| Variable | Required | Purpose |
|---|---:|---|
| `NOOK_DEVICE_ID` | yes | Device ID expected in the `ID` header |
| `NOOK_API_KEY` | yes | Existing Nook `access-token` secret |
| `PUBLIC_BASE_URL` | deployment | Public HTTPS origin without `/api` |
| `REFRESH_RATE_SECONDS` | no | Nook refresh interval; default/minimum 300/60 |
| `SUPABASE_URL` | yes | Supabase project URL |
| `SUPABASE_SECRET_KEY` | yes | Render-only new-format `sb_secret_...` key |
| `SCREEN_SIGNING_SECRET` | yes | Independent high-entropy HMAC secret, at least 32 characters |
| `SCREEN_URL_TTL_SECONDS` | no | Signed image lifetime; default 900, bounded to 60–3600 |

Never commit a real `.env`. `.env.example` contains placeholders only. Do not reuse `NOOK_API_KEY` as `SCREEN_SIGNING_SECRET`.

## Local setup

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:NOOK_DEVICE_ID = "AA:BB:CC:DD:EE:FF"
$env:NOOK_API_KEY = "test-only-local-key"
$env:PUBLIC_BASE_URL = "http://127.0.0.1:8000"
$env:SUPABASE_URL = "https://your-project.supabase.co"
$env:SUPABASE_SECRET_KEY = "sb_secret_server-only-placeholder"
$env:SCREEN_SIGNING_SECRET = "generate-an-independent-random-secret-at-least-32-characters"
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Do not use a real Supabase key for automated tests. Tests inject fake providers and `httpx.MockTransport`; they make no live Supabase requests.

## Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | none | Process health only |
| `GET /api/display` | `ID` + `access-token` | Refresh content and return signed dynamic `image_url` |
| `GET /screen/current.png?v=...&exp=...&sig=...` | short-lived HMAC URL | Return the requested cached/current todo PNG |
| `GET /screen/test.png` | none | Retained Stage 2B-1 orientation diagnostic |

`/api/display` never returns the todo body. A provider or renderer failure returns the most recent successful artifact when available; a cold process with no successful artifact returns 503. Empty todo text is valid and renders `暂无内容` as a new version.

The process-local cache holds at most two successful versions. On a cache miss, the image endpoint reloads Supabase and rebuilds only when the current version matches the signed `v`; stale URLs return 410.

## Renderer

- The renderer preserves manual newlines and wraps Chinese, English, digits, and unbroken strings by measured pixel width.
- It tries even font sizes from 52 px down to 20 px and uses the largest layout that fits inside 44 px margins.
- Pathological excessive line breaks are safely truncated at the minimum size with an ellipsis.
- Output is Pillow mode `1`, white background and black text.
- It first composes upright 600×800, then applies `Image.Transpose.ROTATE_90` to produce the verified 800×600 source PNG.

The bundled font is `assets/fonts/NotoSansCJKsc-Regular.otf`, downloaded from the official [`notofonts/noto-cjk`](https://github.com/notofonts/noto-cjk/tree/main/Sans/OTF/SimplifiedChinese) repository. It is distributed under the SIL Open Font License 1.1; the exact license text is included at `assets/fonts/LICENSE`. No system font discovery is used.

## Tests

Run from `server/`:

```powershell
python -m compileall -q .
python -m unittest discover -s tests -v
```

The suite covers provider REST shape/headers and failures, normalized versions, Chinese/manual/automatic wrapping, 300-character and pathological layouts, exact PNG orientation/size, signing tampering/expiry, `compare_digest`, two-version cache behavior, last-known-good fallback, device authentication, signed image delivery, cache-miss rebuild, stale rejection, and Stage 2B-1 regression.

## Deployment boundary

This implementation has not changed Render or the Nook. Before deployment, add the three required server-only variables to Render:

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
SCREEN_SIGNING_SECRET
```

Optionally add `SCREEN_URL_TTL_SECONDS=900`. Keep the existing four Nook/public URL/refresh variables unchanged. After deployment, verify browser access to `/health`, authenticated `/api/display`, the returned signed PNG, and finally the real editor → Supabase → Render → Nook chain before marking Stage 2B-2 verified.
