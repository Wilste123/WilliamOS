#!/usr/bin/env bash
# Deploy FastAPI to Fly.io. Requires: fly auth login, .env in repo root.
# Usage: ./scripts/deploy-fly.sh [https://your-app.vercel.app]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env in repo root"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-${SUPABASE_KEY:-}}"
if [[ -z "$SUPABASE_ANON_KEY" ]]; then
  echo "Set SUPABASE_ANON_KEY (or SUPABASE_KEY) in .env"
  exit 1
fi

if [[ "$SUPABASE_ANON_KEY" == *"service_role"* ]] || python3 -c "
import base64, json, os, sys
t = os.environ.get('K', '')
try:
    p = t.split('.')[1]
    p += '=' * (-len(p) % 4)
    r = json.loads(base64.urlsafe_b64decode(p)).get('role')
    sys.exit(0 if r == 'service_role' else 1)
except Exception:
    sys.exit(1)
" K="$SUPABASE_ANON_KEY" 2>/dev/null; then
  echo "WARNING: Your Supabase key looks like service_role."
  echo "Use the anon (public) key from Supabase → Settings → API → anon key."
  echo "Add SUPABASE_ANON_KEY=... to .env and re-run."
  exit 1
fi

VERCEL_URL="${1:-}"
CORS="${CORS_ORIGINS:-}"
FRONTEND="${FRONTEND_URL:-}"

if [[ -n "$VERCEL_URL" ]]; then
  CORS="$VERCEL_URL"
  FRONTEND="$VERCEL_URL"
fi

echo "==> Fly auth"
fly auth whoami

APP_NAME="$(grep -E '^app\s*=' fly.toml | sed -E "s/^app[[:space:]]*=[[:space:]]*['\"]([^'\"]+)['\"].*/\1/")"
if [[ -z "$APP_NAME" || "$APP_NAME" == *"="* ]]; then
  echo "Could not read app name from fly.toml"
  exit 1
fi
if ! fly status -a "$APP_NAME" >/dev/null 2>&1; then
  echo "==> Creating Fly app $APP_NAME (first time)"
  if ! fly launch --no-deploy --name "$APP_NAME" --region ams --copy-config --yes; then
    echo ""
    echo "Fly app creation failed. Common fix: add a card at"
    echo "  https://fly.io/dashboard/personal/billing"
    echo "(free tier — required even for \$0 usage)"
    exit 1
  fi
fi

echo "==> Setting Fly secrets"
SECRETS=(
  "OPENAI_API_KEY=${OPENAI_API_KEY}"
  "SUPABASE_URL=${SUPABASE_URL}"
  "SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}"
  "DOCUMENTS_BUCKET=${DOCUMENTS_BUCKET:-documents}"
  "APP_ENV=production"
)
if [[ -n "$CORS" ]]; then
  SECRETS+=("CORS_ORIGINS=${CORS}")
  SECRETS+=("FRONTEND_URL=${FRONTEND}")
fi
if [[ -n "${OPENAI_MODEL:-}" ]]; then
  SECRETS+=("OPENAI_MODEL=${OPENAI_MODEL}")
fi
if [[ -n "${GOOGLE_CLIENT_ID:-}" && -n "${GOOGLE_CLIENT_SECRET:-}" ]]; then
  SECRETS+=("GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}")
  SECRETS+=("GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}")
  if [[ -n "$FRONTEND" ]]; then
    SECRETS+=("GOOGLE_REDIRECT_URI=${FRONTEND%/}/integrations/callback")
  elif [[ -n "${GOOGLE_REDIRECT_URI:-}" ]]; then
    SECRETS+=("GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI}")
  fi
fi

fly secrets set "${SECRETS[@]}" -a "$APP_NAME"

echo "==> Deploying to Fly"
fly deploy -a "$APP_NAME"

echo "==> Health check"
curl -sf "https://${APP_NAME}.fly.dev/health" && echo ""

if [[ -z "$VERCEL_URL" ]]; then
  echo ""
  echo "Next: deploy Vercel, then re-run with your URL:"
  echo "  ./scripts/deploy-fly.sh https://YOUR-APP.vercel.app"
fi
