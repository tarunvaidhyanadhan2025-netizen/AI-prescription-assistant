# RxLens — Integrated Project

New UI with original backend, fully integrated.

## Structure
```
rxlens-integrated/
├── backend/          ← FastAPI backend (untouched)
└── frontend/         ← New UI, wired to backend
```

## Quick Start

### 1. Backend
```bash
cd backend
cp .env.example .env
# Edit .env: set MODEL_PROVIDER=gemini and GEMINI_API_KEY=your-key
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
# .env.local already set to http://localhost:8000
npm run dev
```

Open http://localhost:3000

## Flow
1. Upload prescription image → OCR via `/api/v1/upload`
2. Automatic AI analysis → `/api/v1/analysis`
3. Results displayed with full medicine safety cards
4. History page → `/api/v1/prescriptions`

## Backend Endpoints (unchanged)
- `POST /api/v1/upload` — Upload prescription image
- `POST /api/v1/analysis` — Run full analysis
- `GET  /api/v1/analysis/:id` — Fetch analysis by ID
- `GET  /api/v1/prescriptions` — List history
- `GET  /api/v1/prescriptions/:id` — Get single prescription
- `GET  /api/v1/health` — Health check
