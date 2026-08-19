#!/usr/bin/env bash
# Deploy Next.js to Vercel. Requires: vercel login.
# Vercel project must have Root Directory = "web" (for Git deploys).
# This script runs from repo root so that setting works.
# Usage: ./scripts/deploy-vercel.sh [project-name]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${NEXT_PUBLIC_API_URL:-https://williamos-api.fly.dev}"
PROJECT="${1:-${VERCEL_PROJECT:-william-os}}"

cd "$ROOT"

echo "==> Vercel auth"
npx vercel whoami

if [[ ! -f .vercel/project.json ]]; then
  echo "==> Linking repo root to Vercel project: $PROJECT"
  npx vercel link --project "$PROJECT" --yes
fi

echo "==> Setting NEXT_PUBLIC_API_URL=${API_URL}"
printf '%s' "$API_URL" | npx vercel env add NEXT_PUBLIC_API_URL production --force 2>/dev/null \
  || printf '%s' "$API_URL" | npx vercel env add NEXT_PUBLIC_API_URL production

echo "==> Production deploy (Root Directory: web — set in Vercel project settings)"
npx vercel --prod

echo ""
echo "Production URL: https://william-os-zeta.vercel.app"
echo "Wire CORS on Fly after API is up:"
echo "  ./scripts/deploy-fly.sh https://william-os-zeta.vercel.app"
