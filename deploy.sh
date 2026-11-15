#!/usr/bin/env bash
# ==============================================================================
# FlowETL Production Deployment Script
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  FlowETL — Production Deployment"
echo "============================================================"

# 1. Check or load environment variables
if [ -f .env ]; then
  echo "[-] Loading environment from .env..."
  export $(grep -v '^#' .env | xargs -0 2>/dev/null || true)
else
  echo "[!] No .env file found. Creating from .env.example..."
  cp .env.example .env
fi

# 2. Check if Docker is requested
if [ "${1:-}" == "--docker" ]; then
  echo "[-] Deploying with Docker Compose..."
  docker compose up -d --build
  echo "[✓] Docker deployment completed successfully!"
  echo "    Web UI: http://localhost:${FLOWETL_PORT:-8000}"
  echo "    Check status: docker compose ps"
  exit 0
fi

# 3. Bare-metal / VM deployment with Python venv
echo "[-] Checking Python virtual environment..."
if [ ! -d ".venv" ]; then
  echo "[-] Creating Python virtual environment in .venv..."
  python3 -m venv .venv
fi

echo "[-] Activating .venv and installing/updating production dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create necessary runtime directories
mkdir -p uploads data output

# 5. Run test suite to verify system integrity before startup
echo "[-] Running automated verification test suite..."
pytest tests/ -q --disable-warnings

# 6. Start production server
echo "============================================================"
echo "[✓] Deployment verified and ready!"
echo "    Starting FlowETL Server on ${FLOWETL_HOST:-0.0.0.0}:${FLOWETL_PORT:-8000}..."
echo "============================================================"
export FLOWETL_ENV=production
exec python run_server.py
