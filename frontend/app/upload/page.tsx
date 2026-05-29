'use client'

import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import UploadDropzone from '@/components/UploadDropzone'
import PrescriptionPreview from '@/components/PrescriptionPreview'
import LoadingState from '@/components/LoadingState'
import { usePrescription } from '@/hooks/usePrescription'
import { cn } from '@/lib/utils'
import { ArrowRight, RefreshCw, Shield, AlertCircle, Info, CheckCircle } from 'lucide-react'

const STEPS = [
  { n: 1, label: 'Upload',  statuses: ['uploading', 'processing', 'success'] },
  { n: 2, label: 'Analyse', statuses: ['processing', 'success'] },
  { n: 3, label: 'Results', statuses: ['success'] },
]

export default function UploadPage() {
  const router = useRouter()
  const {
    status, file, previewUrl, ocrText,
    uploadProgress, processingStep, error,
    processFile, reset,
  } = usePrescription()

  // Navigate to results when done
  useEffect(() => {
    if (status === 'success') {
      router.push('/results')
    }
  }, [status, router])

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
      {/* Page header */}
      <div className="mb-8">
        <p className="label-mono text-[#0DCDAA] mb-2" style={{ fontSize: '0.62rem' }}>STEP 1 OF 2</p>
        <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
          Upload Prescription
        </h1>
        <p className="text-sm mt-2" style={{ color: 'hsl(var(--muted-foreground))' }}>
          Upload a photo or scan of your prescription. Supports JPG, PNG, PDF, WEBP, and HEIC.
        </p>
      </div>

      {/* Progress bar */}
      <div className="flex items-center gap-2 mb-8 flex-wrap">
        {STEPS.map(({ n, label, statuses }, i) => {
          const done = statuses.includes(status)
          return (
            <div key={n} className="flex items-center gap-2">
              <div
                className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center border text-xs font-bold transition-all duration-300',
                  done
                    ? 'bg-[#0DCDAA] border-[#0DCDAA] text-[#071A14]'
                    : 'border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]'
                )}
                style={{ background: done ? '#0DCDAA' : 'hsl(var(--secondary))' }}
              >
                {done ? <CheckCircle className="w-4 h-4" /> : n}
              </div>
              <span
                className="label-mono"
                style={{
                  fontSize: '0.62rem',
                  color: done ? '#0DCDAA' : 'hsl(var(--muted-foreground))',
                }}
              >
                {label.toUpperCase()}
              </span>
              {i < STEPS.length - 1 && (
                <div
                  className="h-px w-6 sm:w-10 transition-colors duration-300"
                  style={{ background: done ? 'rgba(13,205,170,0.35)' : 'hsl(var(--border)/0.5)' }}
                />
              )}
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Left panel ── */}
        <div className="space-y-5">
          {(status === 'idle' || status === 'error') && (
            <>
              <UploadDropzone onFileAccepted={processFile} disabled={false} />

              {status === 'error' && error && (
                <div
                  className="flex items-start gap-3 p-4 rounded-xl border"
                  style={{ borderColor: 'rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)' }}
                >
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-red-400">Analysis Failed</p>
                    <p className="text-xs mt-1" style={{ color: 'hsl(var(--muted-foreground))' }}>{error}</p>
                    <button
                      onClick={reset}
                      className="mt-2 flex items-center gap-1.5 text-xs text-[#0DCDAA] hover:underline"
                    >
                      <RefreshCw className="w-3 h-3" /> Try again
                    </button>
                  </div>
                </div>
              )}

              {/* Upload tips */}
              <div
                className="rounded-xl border p-4 space-y-2.5"
                style={{ borderColor: 'hsl(var(--border)/0.5)', background: 'hsl(var(--secondary)/0.2)' }}
              >
                <div className="flex items-center gap-2">
                  <Info className="w-3.5 h-3.5 text-[#3A7FD4]" />
                  <p className="label-mono text-[#3A7FD4]" style={{ fontSize: '0.6rem' }}>TIPS FOR BEST RESULTS</p>
                </div>
                {[
                  'Ensure all text is clearly visible and in focus',
                  'Good lighting significantly improves OCR accuracy',
                  'Crop out background clutter if possible',
                  'Both printed and handwritten prescriptions work',
                ].map((tip, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <div className="w-1 h-1 rounded-full bg-[#0DCDAA]/50 mt-1.5 shrink-0" />
                    <p className="text-xs" style={{ color: 'hsl(var(--muted-foreground))' }}>{tip}</p>
                  </div>
                ))}
              </div>
            </>
          )}

          {status === 'uploading' && (
            <div
              className="rounded-2xl border p-6"
              style={{ borderColor: 'hsl(var(--border)/0.5)', background: 'hsl(var(--card))' }}
            >
              <LoadingState variant="upload" progress={uploadProgress} />
            </div>
          )}

          {status === 'processing' && (
            <div
              className="rounded-2xl border p-6"
              style={{ borderColor: 'rgba(13,205,170,0.2)', background: 'hsl(var(--card))' }}
            >
              <LoadingState variant="processing" step={processingStep} />
              <div
                className="mt-4 pt-4 border-t"
                style={{ borderColor: 'hsl(var(--border)/0.4)' }}
              >
                <button
                  onClick={reset}
                  className="flex items-center gap-1.5 text-xs transition-colors"
                  style={{ color: 'hsl(var(--muted-foreground))' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'hsl(var(--foreground))')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'hsl(var(--muted-foreground))')}
                >
                  <RefreshCw className="w-3 h-3" /> Cancel and start over
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Right panel: preview ── */}
        <div className="space-y-5">
          {previewUrl || ocrText ? (
            <PrescriptionPreview
              previewUrl={previewUrl}
              ocrText={ocrText}
              fileName={file?.name}
            />
          ) : (
            <div
              className="rounded-2xl border-2 border-dashed min-h-[320px] flex flex-col items-center justify-center gap-3 p-8"
              style={{ borderColor: 'hsl(var(--border)/0.35)', background: 'hsl(var(--secondary)/0.1)' }}
            >
              <div
                className="w-16 h-16 rounded-2xl flex items-center justify-center border"
                style={{ background: 'hsl(var(--secondary))', borderColor: 'hsl(var(--border))' }}
              >
                <ArrowRight
                  className="w-6 h-6 rotate-180"
                  style={{ color: 'hsl(var(--muted-foreground))' }}
                />
              </div>
              <p className="text-sm text-center" style={{ color: 'hsl(var(--muted-foreground))' }}>
                Your prescription preview will appear here after uploading.
              </p>
            </div>
          )}

          {/* Privacy callout */}
          <div
            className="flex items-start gap-2.5 p-3.5 rounded-xl border"
            style={{ borderColor: 'hsl(var(--border)/0.4)', background: 'hsl(var(--secondary)/0.15)' }}
          >
            <Shield className="w-4 h-4 text-[#0DCDAA] shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed" style={{ color: 'hsl(var(--muted-foreground))' }}>
              <strong style={{ color: 'hsl(var(--foreground))' }}>Privacy protected.</strong>{' '}
              Your prescription is processed in memory only and never stored on our servers. All analysis is ephemeral.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
