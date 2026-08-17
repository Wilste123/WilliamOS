#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Starting WilliamOS dev stack..."
echo ""
echo "Terminal 1 — FastAPI:"
echo "  cd $ROOT && uvicorn app.api.main:app --reload --port 8000"
echo ""
echo "Terminal 2 — Next.js:"
echo "  cd $ROOT/web && npm run dev"
echo ""
echo "Terminal 3 — iPhone test (optional):"
echo "  ngrok http 3000"
echo "  Open the ngrok URL on iPhone → Add to Home Screen"
echo ""
echo "Do NOT set NEXT_PUBLIC_API_URL when using single ngrok tunnel on :3000."
echo "See docs/IPHONE-TEST.md for details."
