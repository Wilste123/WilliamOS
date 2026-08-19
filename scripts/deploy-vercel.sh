#!/usr/bin/env bash
# Deploy Next.js to Vercel. Requires: vercel login, project linked in web/
# Usage: ./scripts/deploy-vercel.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${NEXT_PUBLIC_API_URL:-https://williamos-api.fly.dev}"

cd "$ROOT/web"

echo "==> Vercel auth"
npx vercel whoami

echo "==> Setting NEXT_PUBLIC_API_URL=${API_URL}"
printf '%s' "$API_URL" | npx vercel env add NEXT_PUBLIC_API_URL production --force 2>/dev/null \
  || printf '%s' "$API_URL" | npx vercel env add NEXT_PUBLIC_API_URL production

echo "==> Production deploy"
npx vercel --prod

echo ""
echo "Copy the production URL above, then wire CORS on Fly:"
echo "  ./scripts/deploy-fly.sh https://YOUR-APP.vercel.app"
