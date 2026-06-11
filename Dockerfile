# =============================================================================
# RxLens — Root Dockerfile (single-container deployment for Render)
# Runs both the FastAPI backend (port 8000) and Next.js frontend (port 3000)
# via supervisord, behind a single exposed port (3000 → frontend).
# The frontend proxies /api/** requests to the backend at localhost:8000.
# =============================================================================

# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Build the Next.js frontend
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /app/frontend

# Copy package files and install ALL dependencies (including devDeps for build)
COPY frontend/package*.json ./
RUN npm install --include=dev

# Copy source code
COPY frontend/ ./

# Set build-time env so Next.js knows the API URL at compile time
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NODE_ENV=production

# Build the standalone Next.js app
RUN npm run build


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Final production image (Python + Node + Tesseract + supervisord)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS final

# ── System packages ──────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-eng \
    # OpenCV system libraries
    libglib2.0-0 \
    libgl1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    # Node.js (for running the standalone Next.js server)
    nodejs \
    npm \
    # Process manager
    supervisor \
    # Misc
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Backend: Python dependencies ─────────────────────────────────────────────
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ .

# Create runtime directories
RUN mkdir -p uploads chroma_db

# ── Frontend: Copy standalone build from builder stage ───────────────────────
WORKDIR /app/frontend

# Copy the compiled standalone Next.js output
COPY --from=frontend-builder /app/frontend/.next/standalone ./
COPY --from=frontend-builder /app/frontend/.next/static ./.next/static
COPY --from=frontend-builder /app/frontend/public ./public

# ── Supervisord configuration ─────────────────────────────────────────────────
# supervisord runs both services and restarts either one if it crashes.
RUN mkdir -p /var/log/supervisor

COPY <<'EOF' /etc/supervisor/conf.d/rxlens.conf
[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:backend]
command=uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
directory=/app/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/backend.err.log
stdout_logfile=/var/log/supervisor/backend.out.log
environment=
    PYTHONUNBUFFERED=1,
    TESSERACT_CMD=/usr/bin/tesseract,
    OCR_PROVIDER=tesseract,
    VECTOR_DB_ENABLED=true,
    CHROMA_PERSIST_DIR=/app/backend/chroma_db,
    UPLOAD_DIR=/app/backend/uploads

[program:frontend]
command=node server.js
directory=/app/frontend
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/frontend.err.log
stdout_logfile=/var/log/supervisor/frontend.out.log
environment=
    NODE_ENV=production,
    PORT=3000,
    HOSTNAME=0.0.0.0
EOF

# ── Expose the frontend port (Render routes external traffic here) ────────────
EXPOSE 3000

# ── Start both services via supervisord ──────────────────────────────────────
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/rxlens.conf"]
