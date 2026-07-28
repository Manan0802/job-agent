#!/usr/bin/env bash
# Put the local app on a public HTTPS URL, for checking it from a phone or
# another machine. Cloudflare's quick tunnel is free and needs no account.
#
# The app itself stays on this laptop: it needs the SQLite file, your resume,
# and a residential IP (job boards throttle datacenter ones). Only the URL is
# remote. See docs/DEPLOY.md for why it is not hosted anywhere.
set -euo pipefail

cd "$(dirname "$0")"

if ! grep -qE '^APP_PASSWORD=.+' .env 2>/dev/null; then
  echo "Refusing to share: APP_PASSWORD is not set in .env."
  echo "Anyone with the URL would get your resume, connections and drafts."
  echo "Set APP_PASSWORD=<something long> and run this again."
  exit 1
fi

if ! command -v cloudflared >/dev/null; then
  echo "cloudflared is not installed. Run: brew install cloudflared"
  exit 1
fi

echo "Starting the app on :8000 ..."
.venv/bin/uvicorn backend.main:app --port 8000 &
app_pid=$!
trap 'kill $app_pid 2>/dev/null' EXIT

until curl -sf http://localhost:8000/health >/dev/null; do sleep 1; done
echo "Up. Opening a tunnel — the trycloudflare.com URL below is your link."
cloudflared tunnel --url http://localhost:8000
