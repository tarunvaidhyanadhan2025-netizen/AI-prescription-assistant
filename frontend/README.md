# RxExplain — AI Prescription Safety Assistant

A production-grade **Next.js 15** frontend for AI-powered prescription analysis.

---

## Stack

| Layer         | Technology                    |
|---------------|-------------------------------|
| Framework     | Next.js 15 (App Router)       |
| Language      | TypeScript 5                  |
| Styling       | Tailwind CSS 3                |
| Icons         | lucide-react                  |
| HTTP client   | Axios                         |
| File upload   | react-dropzone                |
| Animation     | CSS keyframes + Tailwind      |

---

## Quick Start

```bash
cd frontend
npm install
cp .env.local.example .env.local
# set NEXT_PUBLIC_API_URL to your backend
npm run dev
```

App will be available at **http://localhost:3000**

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx            # Root layout + fonts + Navbar/Footer
│   ├── page.tsx              # Landing page (hero + features + CTA)
│   ├── globals.css           # CSS variables, animations, utilities
│   ├── upload/
│   │   └── page.tsx          # Upload wizard page
│   └── results/
│       └── page.tsx          # Analysis results dashboard
├── components/
│   ├── Navbar.tsx            # Sticky responsive nav + dark mode toggle
│   ├── Footer.tsx            # Footer with disclaimer
│   ├── UploadDropzone.tsx    # Drag-and-drop file upload
│   ├── PrescriptionPreview.tsx  # Image preview + OCR text viewer
│   ├── MedicineCard.tsx      # Full medicine detail card (5 tabs)
│   ├── DrowsinessIndicator.tsx  # Driving safety badge + panel
│   ├── SideEffectList.tsx    # Severity-coded side effect browser
│   ├── DosageSafetyCard.tsx  # Dosage grid + missed-dose/overdose info
│   ├── WarningCard.tsx       # Drug interactions + age warnings
│   └── LoadingState.tsx      # Upload progress + processing animation + skeleton
├── hooks/
│   └── usePrescription.ts    # Upload + analysis state machine
├── services/
│   ├── api.ts                # Axios client + endpoint wrappers
│   └── mockData.ts           # Rich dev fixture (3 medicines)
├── types/
│   ├── medicine.ts           # Domain types: Medicine, SideEffect, etc.
│   └── api.ts                # Request / response types
└── lib/
    └── utils.ts              # cn(), severity helpers, formatters
```

---

## Design System

- **Palette**: Dark slate background (#0D111A) with teal (#0DCDAA) + blue (#3A7FD4) accents
- **Typography**: Syne (UI / headings) + JetBrains Mono (labels / code)
- **Theme tokens**: CSS custom properties in `globals.css`; dark-mode first
- **Severity colours**: emerald → amber → orange → red (low → critical)
- **Animations**: fadeUp (staggered cards), scanH (upload/analysis), shimmer (skeletons), warningPulse (critical alerts)

---

## Backend API Contract

Point `NEXT_PUBLIC_API_URL` to your server. Expected endpoints:

### `POST /api/upload`
Multipart file upload.

**Response**
```json
{
  "success": true,
  "fileId": "abc123",
  "fileName": "prescription.jpg",
  "fileSize": 204800,
  "mimeType": "image/jpeg",
  "ocrText": "Dr. Mehta\n...",
  "previewUrl": "/previews/abc123.jpg"
}
```

### `POST /api/analyze`
```json
{
  "fileId": "abc123",
  "rawText": "...",
  "patientAge": 45
}
```

**Response**: `PrescriptionAnalysis` (see `types/medicine.ts`)

### `GET /api/analysis/:id`
Retrieve a previously computed analysis.

> In development the app falls back to `services/mockData.ts` automatically when the API is unreachable.

---

## Accessibility

- All interactive elements carry `aria-label`
- Focus rings on every focusable element (`outline: 2px solid #0DCDAA`)
- Colour contrast meets WCAG AA for body text
- Keyboard-navigable tabs, dropzone, and mobile menu

---

## Key Features

- **Drag-and-drop upload** with file type + size validation
- **OCR preview** with zoom, rotate, and copy-to-clipboard
- **Tabbed medicine cards** (Overview / Dosage / Side Effects / Interactions / Lifestyle)
- **Drowsiness indicator** with driving safety callout
- **Drug interaction checker** with severity badges
- **Age-specific warning panels** (paediatric / geriatric)
- **Dosage safety grid** with missed-dose and overdose warnings
- **Lifestyle recommendations** categorised by diet, alcohol, sleep, driving, etc.
- **Critical alert banner** with warning-pulse animation
- **Filter bar** (All / Critical Only / With Warnings)
- **Download JSON report** + print support
- **Dark mode** (default) with toggle
- **Fully responsive** — mobile, tablet, desktop

---

## Licence

MIT — for educational and informational purposes. Not a substitute for professional medical advice.
