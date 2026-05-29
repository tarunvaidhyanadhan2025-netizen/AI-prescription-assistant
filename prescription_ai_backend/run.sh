#!/usr/bin/env bash
# ============================================================
# AI Prescription Explainer & Safety Assistant
# Local development startup script
# ============================================================

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Colour

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
section() { echo -e "\n${BLUE}━━━ $* ━━━${NC}"; }

# ── Project root ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

section "AI Prescription Explainer & Safety Assistant"

# ── Check Python version ──────────────────────────────────
section "Python Version Check"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_VERSION=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
REQUIRED_MAJOR=3
REQUIRED_MINOR=10

IFS='.' read -r -a PV <<< "$PYTHON_VERSION"
if (( PV[0] < REQUIRED_MAJOR || (PV[0] == REQUIRED_MAJOR && PV[1] < REQUIRED_MINOR) )); then
    error "Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ required. Found: $PYTHON_VERSION"
    exit 1
fi
info "Python $PYTHON_VERSION ✓"

# ── Check Tesseract ───────────────────────────────────────
section "Tesseract OCR Check"
TESSERACT_CMD="${TESSERACT_CMD:-tesseract}"
if command -v "$TESSERACT_CMD" &>/dev/null; then
    TESS_VERSION=$($TESSERACT_CMD --version 2>&1 | head -1)
    info "Tesseract found: $TESS_VERSION ✓"
else
    warn "Tesseract not found at '$TESSERACT_CMD'."
    warn "OCR features will be unavailable."
    warn "Install with:"
    warn "  Ubuntu/Debian: sudo apt install tesseract-ocr"
    warn "  macOS:         brew install tesseract"
    warn "  Windows:       https://github.com/UB-Mannheim/tesseract/wiki"
fi

# ── Virtual environment ───────────────────────────────────
section "Virtual Environment"
VENV_DIR="${VENV_DIR:-.venv}"

if [[ ! -d "$VENV_DIR" ]]; then
    info "Creating virtual environment at ./$VENV_DIR ..."
    $PYTHON_BIN -m venv "$VENV_DIR"
fi

# Activate
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
info "Virtual environment activated ✓"

# ── Install dependencies ──────────────────────────────────
section "Dependencies"
if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
    info "Installing/updating dependencies from requirements.txt ..."
    pip install --quiet --upgrade pip
    pip install --quiet -r requirements.txt
    info "Dependencies installed ✓"
else
    info "Skipping install (SKIP_INSTALL=1)"
fi

# ── Environment file ──────────────────────────────────────
section "Environment Configuration"
if [[ ! -f ".env" ]]; then
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        warn ".env created from .env.example"
        warn "⚠  Please set OPENAI_API_KEY in .env before using AI features."
    else
        warn "No .env or .env.example found. Using defaults."
    fi
else
    info ".env found ✓"
fi

# Check for OpenAI key
if grep -q "sk-your-openai-api-key" .env 2>/dev/null; then
    warn "⚠  OPENAI_API_KEY is not set in .env. AI features require a valid key."
fi

# ── Create runtime directories ────────────────────────────
section "Runtime Directories"
mkdir -p uploads chroma_db logs
info "Directories: uploads/, chroma_db/, logs/ ✓"

# ── Start server ──────────────────────────────────────────
section "Starting Server"

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-1}"
RELOAD="${RELOAD:-true}"

info "Host:    $HOST"
info "Port:    $PORT"
info "Workers: $WORKERS"
info "Reload:  $RELOAD"
info ""
info "API Docs: http://localhost:$PORT/docs"
info "Health:   http://localhost:$PORT/api/v1/health"
info ""
info "Press Ctrl+C to stop."
echo ""

if [[ "$RELOAD" == "true" ]]; then
    uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir app \
        --log-level info
else
    uvicorn app.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --log-level info
fi
