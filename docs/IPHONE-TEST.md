# WilliamOS — iPhone PWA test

Daily use happens on your phone. Test locally before deploy.

## Single ngrok tunnel (recommended)

1. Start FastAPI on port 8000
2. Start Next.js on port 3000
3. Do **not** set `NEXT_PUBLIC_API_URL` in `web/.env.local`
4. Run:

```bash
ngrok http 3000
```

5. Open the ngrok HTTPS URL on iPhone
6. Log in and test: Hjem → Chat → Inbox → Oppgaver → Eiendeler
7. Safari → Share → **Add to Home Screen** (Mini-jarv)

Next.js proxies `/api/*` to `localhost:8000` on your Mac, so the phone never talks to port 8000 directly.

## MVP checklist (Mac + iPhone)

- [ ] Login works
- [ ] Hjem shows net worth + weekly brief
- [ ] Chat streams with quick actions
- [ ] Inbox capture + apply suggestions
- [ ] Task create + complete + edit
- [ ] Asset create + edit updates Hjem net worth
- [ ] Asset detail page shows tasks, documents, timeline
- [ ] Document upload works
- [ ] Assistant name saves in settings
- [ ] Usage stats appear in Innstillinger

## Troubleshooting

| Problem | Fix |
|---------|-----|
| API 401 on phone | Log in again; check ngrok URL matches session origin |
| Backend unreachable | Ensure FastAPI runs on Mac; check `API_PROXY_URL` in `web/.env.local` |
| CORS errors (two tunnels) | Add ngrok frontend URL to `CORS_ORIGINS` in `.env` |

See [docs/GETTING-STARTED.md](../docs/GETTING-STARTED.md) for setup.
