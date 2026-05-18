#!/usr/bin/env bash
# Run the FastAPI backend and Next.js frontend together for local dev.
# Usage: ./dev.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# Start FastAPI backend
echo "→ Starting FastAPI on http://localhost:8000"
"$ROOT/venv/bin/uvicorn" api.main:app --reload --port 8000 &
API_PID=$!

# Start Next.js frontend
echo "→ Starting Next.js on http://localhost:3000"
cd "$ROOT/web"
npm run dev &
WEB_PID=$!

trap 'echo "Stopping..."; kill $API_PID $WEB_PID 2>/dev/null || true; exit 0' INT TERM

wait $API_PID $WEB_PID
