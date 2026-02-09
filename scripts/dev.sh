#!/bin/bash
# Start both the FastAPI backend and Vite dev server for development.
# Usage: ./scripts/dev.sh

set -e

echo "Starting LegacyLipi development servers..."

# Start FastAPI backend
echo "Starting FastAPI backend on http://localhost:8000 ..."
uv run python -m legacylipi.api.main &
BACKEND_PID=$!

# Start Vite dev server
echo "Starting Vite dev server on http://localhost:5173 ..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

echo ""
echo "========================================"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API docs: http://localhost:8000/docs"
echo "========================================"
echo "Press Ctrl+C to stop both servers."

wait
