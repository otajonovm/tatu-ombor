# TATU Brend Do'koni — Telegram Mini App

## Local development

```powershell
cd webapp
Copy-Item .env.example .env
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`. Telegram
requires an HTTPS URL for a real Web App, so local testing should use a
trusted HTTPS tunnel such as Cloudflare Tunnel or ngrok.

## Production build

```powershell
npm run build
```

Deploy `dist/` to an HTTPS static host and set the Python API's:

```env
WEBAPP_URL=https://your-frontend.example
WEBAPI_URL=https://your-api.example
WEBAPP_ORIGINS=https://your-frontend.example
```

The frontend does not contain a Supabase key. It sends Telegram's
`initData` in `X-Telegram-Init-Data`; `web_api.py` verifies it server-side.
