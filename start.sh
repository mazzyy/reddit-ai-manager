#!/bin/bash
# ============================================================
# Reddit AI Content Manager — Quick Start
# ============================================================

set -e

echo "╔══════════════════════════════════════════════╗"
echo "║   Reddit AI Content Manager — Starting...    ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Find a compatible Python (3.10–3.13)
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        echo "✓ Using $candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    # Check if default python3 is in range
    if command -v python3 &>/dev/null; then
        minor=$(python3 -c "import sys; print(sys.version_info.minor)")
        if [ "$minor" -ge 10 ] && [ "$minor" -le 13 ]; then
            PYTHON="python3"
            echo "✓ Using python3 (3.$minor)"
        fi
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "✗ No compatible Python found (need 3.10–3.13)."
    echo "  Python 3.14 is too new — most packages don't support it yet."
    echo ""
    echo "  Fix on macOS:"
    echo "    brew install python@3.13"
    echo ""
    echo "  Then re-run: ./start.sh"
    exit 1
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
    echo "⚠  Created backend/.env from template — edit it with your credentials."
    echo ""
fi

echo "▶ Starting FastAPI backend on :8000..."
cd backend
if [ ! -d "venv" ]; then
    "$PYTHON" -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
python main.py &
BACKEND_PID=$!
cd ..

echo "▶ Starting React frontend on :5173..."
cd frontend
[ ! -d "node_modules" ] && npm install --silent
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✓ Dashboard:  http://localhost:5173         ║"
echo "║  ✓ API:        http://localhost:8000/docs    ║"
echo "║  Default login: admin / admin                ║"
echo "║  Press Ctrl+C to stop                        ║"
echo "╚══════════════════════════════════════════════╝"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait