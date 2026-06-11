// ─── Backend response types (matching FastAPI schemas exactly) ───────────────

export type ApiStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error'

/** POST /api/v1/upload */
export interface UploadResponse {
  prescription_id: string
  filename: string
  raw_text: string
  cleaned_text: string
  detected_medicines: string[]
  ocr_confidence: number
  message: string
}

/** POST /api/v1/analysis  or  GET /api/v1/analysis/:id */
export interface AnalysisRequest {
  prescription_id: string
  patient_age?: number | null
  language?: string
  medicines?: string[] | null
}

export interface MedicineAnalysis {
  medicine_name: string
  explanation: string
  use_case: string
  mechanism: string
  how_to_take: string
  side_effects: string[]
  serious_side_effects: string[]
  causes_drowsiness: boolean
  drowsiness_note: string
  dosage_info: string
  dosage_safe: boolean
  dosage_notes: string[]
  age_warnings: string[]
  contraindications: string[]
  alternatives: string[]
  severity_level: 'low' | 'medium' | 'high' | 'critical' | 'unknown'
  rag_sources: string[]
  drug_class: string
  generated_by: string
}

export interface FullAnalysisResponse {
  prescription_id: string
  patient_age: number | null
  language: string
  medicines: MedicineAnalysis[]
  overall_drowsiness_warning: boolean
  overall_dosage_concern: boolean
  overall_age_warning: boolean
  overall_severity: string
  total_medicines_analysed: number
  provider_used: string
  summary: string
}

/** GET /api/v1/prescriptions */
export interface PrescriptionSummary {
  prescription_id: string
  detected_medicines: string[]
  ocr_confidence: number
  patient_age: number | null
  language: string
  doctor_name: string
  notes: string
}

export interface PrescriptionListResponse {
  total: number
  prescriptions: PrescriptionSummary[]
}

/** GET /api/v1/health */
export interface HealthResponse {
  status: string
  version: string
  provider: string
  vector_db_enabled: boolean
  ocr_provider: string
  details: Record<string, unknown>
}

export interface ApiError {
  code?: string
  message?: string
  detail?: string | unknown
}
