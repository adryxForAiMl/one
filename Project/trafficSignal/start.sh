#!/usr/bin/env bash
# Traffic Simulator One-Command Launcher (API + Web Dashboard)
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

echo "=== Traffic Signal Simulator ==="
echo "Workspace: $ROOT"

# Ensure venv python is available
if [ -f "$ROOT/.venv/bin/python3" ]; then
    PYTHON="$ROOT/.venv/bin/python3"
else
    PYTHON="python3"
fi

# Cleanup background processes on exit
cleanup() {
    echo ""
    echo "Stopping Traffic services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

echo "1. Starting FastAPI backend on http://127.0.0.1:8000 ..."
PYTHONPATH="$ROOT" "$PYTHON" -m Traffic.api --host 127.0.0.1 --port 8000 &

echo "2. Starting Vite web dashboard on http://127.0.0.1:5173 ..."
npm --prefix "$DIR/web" run dev &

sleep 2
echo ""
echo "Traffic Signal Control Center is LIVE:"
echo "  -> Web Dashboard:  http://127.0.0.1:5173"
echo "  -> Backend API:    http://127.0.0.1:8000"
echo "  -> API Docs:       http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

wait

