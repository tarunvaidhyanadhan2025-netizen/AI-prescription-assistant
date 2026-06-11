#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Render build script for RxLens backend
# Installs Tesseract OCR (system binary) then Python dependencies.
# ─────────────────────────────────────────────────────────────────────────────
set -e  # exit immediately on any error

echo "──────────────────────────────────────────"
echo " RxLens Backend — Render Build Script"
echo "──────────────────────────────────────────"

echo "[1/3] Installing system dependencies (Tesseract OCR + OpenCV libs)..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev
rm -rf /var/lib/apt/lists/*

echo "[2/3] Installing Python dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "[3/3] Creating required directories..."
mkdir -p uploads chroma_db

echo "✅ Build complete."
