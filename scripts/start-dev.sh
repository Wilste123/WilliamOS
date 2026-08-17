#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "Mini-jarv dev stack"
echo ""
echo "1. API:    uvicorn app.api.main:app --reload --port 8000"
echo "2. Web:    cd web && npm run dev:clean"
echo "3. Phone:  ngrok http 3000"
echo ""
echo "Docs: $ROOT/docs/GETTING-STARTED.md"
