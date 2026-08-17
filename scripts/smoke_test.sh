#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Running pytest"
python3 -m pytest tests/ -q

echo "==> Checking FastAPI health (optional — start server first)"
if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
  curl -s http://127.0.0.1:8000/health
  echo ""
  echo "FastAPI: OK"
else
  echo "FastAPI not running on :8000 — skip (start with: uvicorn app.api.main:app --reload --port 8000)"
fi

echo "==> Checking Next.js (optional — start dev server first)"
if curl -sf http://127.0.0.1:3000/login >/dev/null 2>&1; then
  echo "Next.js: OK"
else
  echo "Next.js not running on :3000 — skip (start with: cd web && npm run dev)"
fi

echo ""
echo "Smoke test complete."
