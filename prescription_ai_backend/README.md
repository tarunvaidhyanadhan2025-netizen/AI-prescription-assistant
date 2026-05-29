# AI Prescription Explainer & Safety Assistant

> **Hackathon MVP** — Upload a prescription image, get an instant AI-powered safety report.

---

## Features

| Feature | Description |
|---|---|
| 📷 **Image Upload** | JPEG, PNG, TIFF, BMP, WEBP support |
| 🔍 **OCR Extraction** | Tesseract-powered text extraction with image preprocessing |
| 💊 **Medicine Detection** | Regex + LLM correction of OCR errors |
| 📖 **Medicine Explanation** | Plain-language, patient-friendly explanations |
| ⚠️ **Side Effects** | Common and serious side effects |
| 😴 **Drowsiness Detection** | Flags medicines that impair driving/operating machinery |
| 💉 **Dosage Safety** | Rule-based + LLM dosage safety checks |
| 👶👴 **Age-Specific Warnings** | Paediatric, geriatric, and pregnancy warnings |
| 🔄 **Alternatives** | Suggests therapeutic alternatives |
| 🧠 **RAG Pipeline** | ChromaDB vector store + OpenAI embeddings |
| 🌍 **Multilingual** | English, Tamil, Hindi, French, Spanish, German, Chinese, Arabic |

---

## Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory + lifespan
│   ├── config.py                # Pydantic settings (env-driven)
│   ├── routes/
│   │   ├── upload.py            # POST /api/v1/upload
│   │   ├── analysis.py          # GET|POST /api/v1/analysis
│   │   └── health.py            # GET /api/v1/health
│   ├── services/
│   │   ├── ocr_service.py       # Tesseract OCR pipeline
│   │   ├── medicine_service.py  # Local DB + OpenAI lookup
│   │   ├── dosage_service.py    # Rule-based dosage safety
│   │   ├── warning_service.py   # Age/drowsiness warnings
│   │   ├── rag_service.py       # ChromaDB RAG retrieval
│   │   └── explanation_service.py # LangChain explanations
│   ├── agents/
│   │   ├── ocr_agent.py         # LLM OCR text refinement
│   │   ├── retrieval_agent.py   # Multi-strategy RAG retrieval
│   │   ├── safety_agent.py      # Comprehensive safety eval
│   │   └── explanation_agent.py # Patient-friendly explanations
│   ├── database/
│   │   ├── chroma.py            # ChromaDB client
│   │   ├── vector_store.py      # Embedding + query logic
│   │   └── medicine_seed.json   # 20 medicines seed data
│   ├── models/
│   │   ├── prescription.py      # Upload request/response
│   │   ├── medicine.py          # Medicine record model
│   │   └── response.py          # Analysis response models
│   ├── prompts/
│   │   ├── explanation_prompt.py
│   │   ├── safety_prompt.py
│   │   └── retrieval_prompt.py
│   ├── utils/
│   │   ├── parser.py            # OCR text parsing
│   │   ├── logger.py            # Structured logging
│   │   └── validators.py        # Input validation
│   └── tests/
│       ├── test_upload.py
│       └── test_analysis.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── run.sh
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **Tesseract OCR**

```bash
# Ubuntu / Debian
sudo apt install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows
# Download installer: https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Clone & Configure

```bash
git clone <your-repo-url>
cd backend

cp .env.example .env
# Edit .env — set your OPENAI_API_KEY
```

### 3. Run (Development)

```bash
bash run.sh
```

The script will:
- Check Python & Tesseract versions
- Create a virtual environment
- Install all dependencies
- Start Uvicorn with hot-reload

API available at: **http://localhost:8000**  
Swagger docs at: **http://localhost:8000/docs**

---

## API Reference

### `POST /api/v1/upload`

Upload a prescription image.

**Form fields:**
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | ✅ | Prescription image |
| `patient_age` | int | ❌ | Patient age (enables age warnings) |
| `language` | string | ❌ | Response language (default: `en`) |

**Response:**
```json
{
  "prescription_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "detected_medicines": ["Amoxicillin", "Paracetamol"],
  "raw_text": "Rx\nAmoxicillin 500mg TID\n...",
  "ocr_confidence": 0.87,
  "message": "Prescription uploaded. Call /analysis/{id} for the safety report."
}
```

---

### `GET /api/v1/analysis/{prescription_id}`

Run full AI analysis on an uploaded prescription.

**Query params:** `patient_age`, `language`

---

### `POST /api/v1/analysis`

Run analysis with an explicit medicine list (bypass OCR).

```json
{
  "prescription_id": "3fa85f64-...",
  "patient_age": 8,
  "language": "en",
  "medicines": ["Aspirin", "Codeine"]
}
```

**Response:**
```json
{
  "prescription_id": "...",
  "medicines": [
    {
      "medicine_name": "Aspirin",
      "explanation": "Aspirin is used for pain relief...",
      "side_effects": ["GI irritation", "Nausea"],
      "causes_drowsiness": false,
      "dosage_info": "300–900mg every 4–6 hours",
      "dosage_safe": true,
      "age_warnings": ["CONTRAINDICATED in children under 16 — Reye's syndrome risk"],
      "alternatives": ["Paracetamol", "Ibuprofen"],
      "severity_level": "critical"
    }
  ],
  "overall_drowsiness_warning": false,
  "overall_age_warning": true,
  "overall_severity": "critical",
  "summary": "⚠ Age-specific warning present."
}
```

---

### `GET /api/v1/health`

Liveness probe.

---

## Docker

```bash
# Build
docker build -t prescription-ai .

# Run
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -v $(pwd)/uploads:/home/appuser/app/uploads \
  -v $(pwd)/chroma_db:/home/appuser/app/chroma_db \
  prescription-ai
```

---

## Testing

```bash
# Activate venv
source .venv/bin/activate

# Run all tests with coverage
pytest app/tests/ -v --cov=app --cov-report=term-missing

# Run specific test file
pytest app/tests/test_upload.py -v
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key |
| `TESSERACT_CMD` | ✅ | Path to Tesseract binary |
| `OPENAI_MODEL` | ❌ | Default: `gpt-4o` |
| `CHROMA_PERSIST_DIR` | ❌ | Default: `./chroma_db` |
| `DEFAULT_LANGUAGE` | ❌ | Default: `en` |

---

## Supported Languages

`en` English · `ta` Tamil · `hi` Hindi · `fr` French · `es` Spanish · `de` German · `zh` Chinese · `ar` Arabic

---

## Medicine Seed Database

20 medicines pre-loaded with full clinical data:
Paracetamol, Amoxicillin, Ibuprofen, Metformin, Atorvastatin, Omeprazole,
Lisinopril, Amlodipine, Aspirin, Cetirizine, Metronidazole, Salbutamol,
Codeine, Diazepam, Levothyroxine, Ciprofloxacin, Prednisolone, Sertraline,
Warfarin, Insulin.

Unknown medicines are automatically looked up via OpenAI and embedded into the vector store.

---

## Safety Disclaimer

> This tool is intended for **educational and informational purposes only**.
> It does **not** constitute medical advice. Always consult a qualified
> healthcare professional before making any decisions about medications.
