export type ApiStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error'

export interface UploadResponse {
  success: boolean
  fileId: string
  fileName: string
  fileSize: number
  mimeType: string
  previewUrl?: string
  ocrText?: string
  message?: string
}

export interface AnalysisRequest {
  fileId?: string
  rawText?: string
  patientAge?: number
  patientWeight?: number
  existingConditions?: string[]
  currentMedications?: string[]
}

export interface AnalysisResponse {
  success: boolean
  data?: import('./medicine').PrescriptionAnalysis
  error?: string
  processingTimeMs?: number
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}
