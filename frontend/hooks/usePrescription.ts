'use client'

import { useState, useCallback, useRef } from 'react'
import type { ApiStatus } from '@/types/api'
import type { PrescriptionAnalysis } from '@/types/medicine'
import { uploadPrescription, mockAnalyzePrescription } from '@/services/api'

interface PrescriptionState {
  status: ApiStatus
  file: File | null
  previewUrl: string | null
  ocrText: string | null
  analysis: PrescriptionAnalysis | null
  uploadProgress: number
  error: string | null
  processingStep: string
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
    }, 550)
  }, [update])

  const stopSteps = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null }
  }, [])

  const processFile = useCallback(async (file: File) => {
    const previewUrl = URL.createObjectURL(file)
    update({ status: 'uploading', file, previewUrl, error: null, uploadProgress: 0, analysis: null, ocrText: null })

    try {
      let ocrText: string | null = null
      try {
        const up = await uploadPrescription(file, (pct) => update({ uploadProgress: pct }))
        ocrText = up.ocrText ?? null
        update({ ocrText, uploadProgress: 100 })
      } catch {
        // dev fallback — skip real upload
        update({ uploadProgress: 100 })
      }

      update({ status: 'processing' })
      startSteps()

      const result = await mockAnalyzePrescription({ rawText: ocrText ?? undefined })
      stopSteps()

      if (result.success && result.data) {
        update({ status: 'success', analysis: result.data, processingStep: '' })
      } else {
        throw new Error(result.error ?? 'Analysis failed.')
      }
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
    if (state.previewUrl) URL.revokeObjectURL(state.previewUrl)
    setState(INITIAL)
  }, [state.previewUrl, stopSteps])

  return { ...state, processFile, reset }
}
