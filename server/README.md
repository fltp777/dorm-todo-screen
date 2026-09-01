# Stage 2B-1 BYOS server

This directory is intentionally independent from the existing GitHub Pages frontend. It implements only:

`Nook -> GET /api/display -> fixed test-screen.png`

It does not read Supabase or render todo text. Dynamic content starts in Stage 2B-2.

## Protocol verified against Nook client v0.16.0

- Easy Setup normalizes the API Base URL to end in `/api`; the client requests `/api/display`.
- Authentication headers are `ID` and `access-token`.
- `Percent-Charged` and `rssi` may also be sent but are not authentication inputs.
- The response uses `image_url` and optional `refresh_rate`. `filename` is returned for diagnostics/interoperability, though v0.16.0 does not read it.
- The image fetch does **not** repeat the auth headers. The fixed calibration PNG is therefore intentionally public in this stage.
- Exact `800x600` images are rotated clockwise by v0.16.0. The generated source PNG is pre-rotated counterclockwise so the expected physical result is upright `600x800` portrait.

Source checked: `usetrmnl/trmnl-nook-simple-touch` tag `v0.16.0`, commit `a1a102dc779c8e57d78ea9ae2b33d9b21bb315af`.

## Local setup (PowerShell)

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:NOOK_DEVICE_ID = "AA:BB:CC:DD:EE:FF"
$env:NOOK_API_KEY = "replace-with-a-long-random-value"
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

Do not commit a real `.env`. Generate a key, for example:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

For local requests, omit `PUBLIC_BASE_URL`; the API derives the current request origin. After deployment, set it to the public HTTPS origin without `/api`, for example `https://example-host.invalid`.

## Endpoints

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /health` | none | Process health |
| `GET /api/display` | `ID` + `access-token` | BYOS display response |
| `GET /screen/test.png` | none | Fixed Stage 2B-1 calibration image |

Example:

```powershell
curl.exe http://127.0.0.1:8000/health
curl.exe -H "ID: AA:BB:CC:DD:EE:FF" -H "access-token: replace-with-a-long-random-value" http://127.0.0.1:8000/api/display
```

Run the built-in test suite from this directory:

```powershell
python -m unittest discover -s tests -v
```

Regenerate the static calibration image only when its layout or dimensions change:

```powershell
python renderer/generate_test_screen.py
```

## Nook Easy Setup after deployment

- **API BASE URL:** public HTTPS origin, such as `https://your-service.example`. Entering the origin or the same URL ending in `/api` is accepted by v0.16.0; do not append `/display`.
- **MAC ADDRESS:** use the device ID shown by the Nook/TRMNL setup screen (normally the Nook Wi-Fi MAC), and set the same value as `NOOK_DEVICE_ID` on the server.
- **DEVICE API KEY:** generate a long random value, store it as `NOOK_API_KEY` on the server, and enter exactly the same value on the Nook.

The final public service must provide a certificate/TLS chain that the Android 2.1-era client can negotiate. Browser success alone does not prove Nook TLS compatibility; that remains an on-device acceptance test.

## Lightweight deployment candidates (not deployed yet)

Set the service/work directory to `server`. With Koyeb Buildpack, leave **Build Command** blank: the root `requirements.txt` triggers Python detection and dependency installation automatically. Use this Run Command:

```text
uvicorn app:app --host 0.0.0.0 --port $PORT
```

In every platform dashboard, set `NOOK_DEVICE_ID`, `NOOK_API_KEY`, `PUBLIC_BASE_URL`, and optionally `REFRESH_RATE_SECONDS`. Never paste secrets into build commands or repository files.

1. **Koyeb free instance — first trial candidate.** Koyeb has an official FastAPI deployment path, supplies a TLS-enabled `*.koyeb.app` URL, and currently offers one free web instance. The free instance scales to zero after one hour without traffic, so the first Nook request after idle may be delayed. Select a root route `/`; do not configure a Koyeb `/api` route because Koyeb strips route prefixes. [FastAPI guide](https://www.koyeb.com/docs/deploy/fastapi) · [free instance limits](https://www.koyeb.com/docs/reference/instances) · [TLS](https://www.koyeb.com/docs/reference/edge-network)
2. **Render free web service — easiest fallback.** Render officially supports FastAPI, provides an `onrender.com` HTTPS URL, and its free web service spins down after 15 idle minutes; waking can take about one minute. That cold start may exceed the old Nook client's practical patience, so test it before relying on it. [FastAPI guide](https://render.com/docs/deploy-fastapi) · [free limits](https://render.com/docs/free) · [TLS](https://render.com/docs/tls)
3. **Railway — low-cost fallback if cold starts fail.** Railway supports FastAPI and generated HTTPS domains. Its current Free plan includes $1 monthly credit; Hobby is $5/month with $5 included usage. It is useful for testing an always-available small service, but billing limits must be configured and reviewed. [FastAPI guide](https://docs.railway.com/guides/fastapi) · [public networking](https://docs.railway.com/networking/public-networking) · [pricing](https://docs.railway.com/pricing/plans)

None of these platforms guarantees stable reachability from every mainland China ISP. Before choosing one, test `/health`, the PNG URL, and finally the Nook itself on the actual dorm Wi-Fi. The decisive risk is not FastAPI support but mainland routing plus Android 2.1-era TLS compatibility.
