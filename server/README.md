# Stage 2B-2 dynamic BYOS server

Status: **COMPLETED / VERIFIED**. Stage 2B-1 remains device-verified, and the Stage 2B-2 dynamic Supabase path has now passed real end-to-end testing on a Nook Simple Touch BNRV300.

Battery display addition: **LOCAL IMPLEMENTATION ONLY**. It has automated local coverage but has not been deployed to Render or device-verified.

Stage 2C flow information screen: **COMPLETED / VERIFIED**. The user reports
that the Flow/Yijing screen has been deployed and verified on the Nook. The
night-sleep schedule below remains local implementation only until separately
deployed and device-tested.

```text
screen_state.main
  → TodoProvider
  → NormalizedContent(todo, reminders, Yijing position, updated_at)
  → 600x800 black/white portrait
  → counterclockwise pre-rotation
  → cached 800x600 PNG
  → short-lived signed image URL
  → TRMNL v0.16.0 clockwise rotation
  → 600x800 Nook portrait
```

The existing GitHub Pages frontend, Supabase Auth/RLS, and Stage 2B-1 calibration image are intentionally unchanged.

## Real-device verification

- Render built and started the FastAPI service successfully; public `/health` and authenticated `/api/display` requests passed.
- The deployed server read `screen_state.main` from the real Supabase project, not from a mock or test fixture.
- `/api/display` returned a dynamic image URL containing `v`, `exp`, and `sig`; the signed URL was successfully opened over public HTTPS.
- The browser and TRMNL Nook Client v0.16.0 downloaded the rendered PNG, and the BNRV300 displayed the same real content entered from the phone editor.
- Chinese, English, the bundled CJK font, and user-authored line breaks rendered correctly.
- The already verified 800×600 pre-rotation rule remains unchanged and produced the correct final Nook display.
- The verified network path used a phone hotspot. Campus PEAP remains a separate follow-up task.

## Security model

- The Nook continues to authenticate `GET /api/display` with `ID` and `access-token`.
- The server reads only `screen_state?id=eq.main&select=text,daily_reminder_text,yijing_position,updated_at`.
- A new `sb_secret_...` Supabase server key is sent only in the REST `apikey` header. It is not a JWT and is never sent as a Bearer token.
- The server key and signing secret must exist only as secret Render environment variables. They never appear in URLs, responses, logs, frontend files, or Nook settings.
- The Nook client does not forward API auth headers when fetching `image_url`. Dynamic images therefore use a short-lived HMAC-SHA256 capability URL.
- `Percent-Charged` is accepted only as an optional canonical integer from 0 to 100. It is request-only device state: never written to Supabase, returned as content, or logged with its raw value.
- The signed capability URL carries non-sensitive `b` (`0..100` or `none`) and `r` (UTC request minute) states. They rebuild the exact battery and `更新 HH:MM` footer after a cache miss; both are HMAC-protected.
- `/screen/test.png` remains public only as a non-private Stage 2B-1 diagnostic artifact.

Canonical image signature input:

```text
GET
/screen/current.png
v=<20-char version>
b=<0..100|none>
r=<UTC-minute|none>
exp=<unix-seconds>
```

The signature is URL-safe Base64 without padding and is verified with `hmac.compare_digest`.

## Environment variables

| Variable | Required | Purpose |
|---|---:|---|
| `NOOK_DEVICE_ID` | yes | Device ID expected in the `ID` header |
| `NOOK_API_KEY` | yes | Existing Nook `access-token` secret |
| `PUBLIC_BASE_URL` | deployment | Public HTTPS origin without `/api` |
| `REFRESH_RATE_SECONDS` | no | Daytime Nook refresh interval; default/minimum 1800/60 |
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
| `GET /screen/current.png?v=...&b=...&r=...&exp=...&sig=...` | short-lived HMAC URL | Return the requested cached/current todo PNG |
| `GET /screen/test.png` | none | Retained Stage 2B-1 orientation diagnostic |

`/api/display` never returns content text. A provider or renderer failure returns the most recent successful artifact when available; a cold process with no successful artifact returns 503.

The process-local cache holds at most two successful versions. A render version includes content `updated_at`, request battery state, and the successful `/api/display` response minute. On a cache miss, the image endpoint rebuilds only when signed `v`, `b`, and `r` still match; stale URLs return 410.

## Dynamic night sleep schedule

`REFRESH_RATE_SECONDS` remains the normal daytime interval (currently 1800
seconds). Each successful `/api/display` response independently chooses its
next delay using an explicit Asia/Shanghai UTC+8 business clock:

- `[07:10, 22:40)` returns the configured daytime value.
- From `22:40` through the following `07:09`, it returns the exact positive
  number of seconds until the next local `07:10`.

Nighttime requests still render and sign the current image normally; only the
response's existing `refresh_rate` field changes. The schedule does not change
the footer time, URL TTL, signed URL shape, cache key, or cache size. A schedule
calculation failure logs a warning and falls back to the configured daytime
value, rather than failing the display request.

## Stage 2C flow renderer

- The upright production layout uses `renderer/flow_layout.py`: x=392 and footer y=746 remain fixed, but there is no production `y=373` horizontal split. The left column flows as todo title → todo → 1 px divider → Yijing header → Yijing paragraphs.
- The entire left column uses one shared `left_font_size` candidate (40→22 px, 2 px steps): todo title, todo body, Yijing heading, trigram/name/line heading, and every Yijing paragraph all use that size. Only bold weight distinguishes headings. The right reminder column remains independently 50→24 px.
- The divider is calculated after the final todo line, with 10 px before/after gaps. If every left size reaches its minimum, the final visible line is ellipsized and a low-sensitivity warning is emitted; no content crosses a divider or footer.
- `yijing_catalog.py` reads `yijing database/yijing_64_hexagrams.json` and flattens 64 whole-hexagram pages, 384 regular lines, plus 乾用九 and 坤用六: 450 bounded manual positions. Database text, punctuation, and traditional characters are preserved.
- The bundled font does not provide usable hexagram/trigram glyphs. The renderer therefore draws generic 1-bit yin/yang geometry from each page's upper/lower trigram names; it does not alter classical text.
- The footer's left `更新 HH:MM` is the server-confirmed `/api/display` response time in UTC+8, never `screen_state.updated_at`. The right battery text keeps the existing thresholds.
- Output is Pillow mode `1`, white background and black text.
- It first composes upright 600×800, then applies `Image.Transpose.ROTATE_90` to produce the verified 800×600 source PNG.
- The fixed footer starts at y=746. It uses 19 px text: content update time at left and valid battery text at right. Missing/invalid battery values render no right footer.

The bundled font is `assets/fonts/NotoSansCJKsc-Regular.otf`, downloaded from the official [`notofonts/noto-cjk`](https://github.com/notofonts/noto-cjk/tree/main/Sans/OTF/SimplifiedChinese) repository. It is distributed under the SIL Open Font License 1.1; the exact license text is included at `assets/fonts/LICENSE`. No system font discovery is used.

## Tests

Run from `server/`:

```powershell
python -m compileall -q .
python -m unittest discover -s tests -v
```

The suite covers provider REST shape/headers and failures, normalized versions, Chinese/manual/automatic wrapping, 300-character and pathological layouts, exact PNG orientation/size, signing tampering/expiry, `compare_digest`, two-version cache behavior, last-known-good fallback, device authentication, signed image delivery, cache-miss rebuild, stale rejection, and Stage 2B-1 regression.

For local visual review, run `python generate_flow_production_previews.py`.
It writes five upright 600×800 production-renderer images and `flow_metadata.json`
under `production_previews/`; they do not pass through FastAPI or become Nook assets.

## Schema status

`../supabase/stage-2c-fixed-v2-state.sql` has been manually executed and
verified by the user in the intended Supabase project: the existing `main` row
retained its text, while `daily_reminder_text=''` and `yijing_position=0` were
added. The SQL only adds those columns, their authenticated column update grant,
and bounds checks; it does not create a table or change RLS policies. Before a
future Pages/Render deployment, the formal JSON must be committed at
`yijing database/yijing_64_hexagrams.json`; the loader resolves only that
repository-relative path.

## Deployment status and boundary

The real Render deployment uses the following server-only variables; their values must remain only in Render and must never be copied into this repository:

```text
SUPABASE_URL
SUPABASE_SECRET_KEY
SCREEN_SIGNING_SECRET
```

`SCREEN_URL_TTL_SECONDS=900` remains optional. The existing Nook/public URL variables are retained, and the configured daytime refresh interval is 1800 seconds. The real editor → Supabase → Render → signed PNG → Nook chain is verified. Render Free spin-down/cold-start behavior has not yet been observed long term, Auto-Deploy is currently Off, and the night-sleep schedule remains pending deployment/device validation.
