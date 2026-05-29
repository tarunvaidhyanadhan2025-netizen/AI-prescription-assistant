import axios from 'axios'
import type { UploadResponse, AnalysisRequest, AnalysisResponse } from '@/types/api'
import type { PrescriptionAnalysis } from '@/types/medicine'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.error ||
      error.message ||
      'An unexpected error occurred.'
    return Promise.reject(new Error(message))
  }
)

export async function uploadPrescription(
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)

  const { data } = await apiClient.post<UploadResponse>('/api/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return data
}

export async function analyzePrescription(request: AnalysisRequest): Promise<AnalysisResponse> {
  const { data } = await apiClient.post<AnalysisResponse>('/api/analyze', request)
  return data
}

export async function getAnalysis(id: string): Promise<PrescriptionAnalysis> {
  const { data } = await apiClient.get<{ data: PrescriptionAnalysis }>(`/api/analysis/${id}`)
  return data.data
}

export async function healthCheck(): Promise<{ status: string }> {
  const { data } = await apiClient.get('/health')
  return data
}

// ─── Mock (dev fallback) ──────────────────────────────────────────────────────
export async function mockAnalyzePrescription(
  _request: AnalysisRequest
): Promise<AnalysisResponse> {
  await new Promise((r) => setTimeout(r, 2600))
  const { MOCK_ANALYSIS } = await import('./mockData')
  return { success: true, data: MOCK_ANALYSIS, processingTimeMs: 2600 }
}

export default apiClient
