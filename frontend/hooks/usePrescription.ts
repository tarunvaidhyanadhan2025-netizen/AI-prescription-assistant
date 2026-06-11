'use client'

import { useState, useCallback, useRef } from 'react'
import type { ApiStatus } from '@/types/api'
import type { PrescriptionAnalysis } from '@/types/medicine'
import {
  uploadPrescription,
  analysePresciption,
  adaptBackendToUI,
  parseApiError,
} from '@/services/api'

interface PrescriptionState {
  status: ApiStatus
  file: File | null
  previewUrl: string | null
  ocrText: string | null
  analysis: PrescriptionAnalysis | null
  uploadProgress: number
  error: string | null
  processingStep: string
  prescriptionId: string | null
}

const INITIAL: PrescriptionState = {
  status: 'idle',
  file: null,
  previewUrl: null,
  ocrText: null,
  analysis: null,
  uploadProgress: 0,
  error: null,
  processingStep: '',
  prescriptionId: null,
}

const STEPS = [
  'Extracting text from prescription…',
  'Identifying medications…',
  'Querying drug database…',
  'Analysing drug interactions…',
  'Generating safety report…',
]

export function usePrescription() {
  const [state, setState] = useState<PrescriptionState>(INITIAL)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const update = useCallback((patch: Partial<PrescriptionState>) => {
    setState((prev) => ({ ...prev, ...patch }))
  }, [])

  const startSteps = useCallback(() => {
    let i = 0
    update({ processingStep: STEPS[0] })
    timerRef.current = setInterval(() => {
      i = (i + 1) % STEPS.length
      update({ processingStep: STEPS[i] })
    }, 700)
  }, [update])

  const stopSteps = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }, [])

  const processFile = useCallback(async (file: File) => {
    const previewUrl = URL.createObjectURL(file)
    update({
      status: 'uploading',
      file,
      previewUrl,
      error: null,
      uploadProgress: 0,
      analysis: null,
      ocrText: null,
      prescriptionId: null,
    })

    try {
      // ── Step 1: Upload + OCR ────────────────────────────────────────────
      let prescriptionId: string
      let ocrText: string | null = null

      try {
        const uploadResult = await uploadPrescription(file, (pct) =>
          update({ uploadProgress: pct })
        )
        prescriptionId = uploadResult.prescription_id
        ocrText = uploadResult.cleaned_text || uploadResult.raw_text || null
        update({ ocrText, uploadProgress: 100, prescriptionId })
      } catch (uploadErr) {
        throw new Error(parseApiError(uploadErr))
      }

      // ── Step 2: Analysis ────────────────────────────────────────────────
      update({ status: 'processing' })
      startSteps()

      let fullAnalysis
      try {
        fullAnalysis = await analysePresciption({
          prescription_id: prescriptionId,
          language: 'en',
        })
      } catch (analysisErr) {
        stopSteps()
        throw new Error(parseApiError(analysisErr))
      }

      stopSteps()

      // ── Step 3: Adapt to UI types ───────────────────────────────────────
      const uiAnalysis = adaptBackendToUI(fullAnalysis)
      // Attach OCR text to analysis
      if (ocrText) uiAnalysis.rawText = ocrText

      update({ status: 'success', analysis: uiAnalysis, processingStep: '' })

    } catch (err) {
      stopSteps()
      update({
        status: 'error',
        error: err instanceof Error ? err.message : 'Unknown error occurred.',
        processingStep: '',
      })
    }
  }, [update, startSteps, stopSteps])

  const reset = useCallback(() => {
    stopSteps()
    setState((prev) => {
      if (prev.previewUrl) URL.revokeObjectURL(prev.previewUrl)
      return INITIAL
    })
  }, [stopSteps])

  return { ...state, processFile, reset }
}
