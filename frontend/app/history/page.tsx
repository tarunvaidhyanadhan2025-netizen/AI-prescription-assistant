'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { listPrescriptions, getAnalysis, adaptBackendToUI, parseApiError } from '@/services/api'
import type { PrescriptionSummary } from '@/types/api'
import { cn } from '@/lib/utils'
import {
  History, Pill, Clock, ChevronRight, UploadCloud,
  AlertCircle, RefreshCw, FileText, User,
} from 'lucide-react'

export default function HistoryPage() {
  const [prescriptions, setPrescriptions] = useState<PrescriptionSummary[]>([])
  const [total, setTotal]                 = useState(0)
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState<string | null>(null)
  const [loadingId, setLoadingId]         = useState<string | null>(null)

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listPrescriptions(20, 0)
      setPrescriptions(res.prescriptions)
      setTotal(res.total)
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchHistory() }, [])

  const handleView = async (id: string) => {
    setLoadingId(id)
    try {
      const full = await getAnalysis(id)
      const ui = adaptBackendToUI(full)
      sessionStorage.setItem('rxlens_analysis', JSON.stringify(ui))
      window.location.href = '/results'
    } catch (err) {
      setError(parseApiError(err))
    } finally {
      setLoadingId(null)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
      <div className="space-y-1.5">
        <p className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.62rem' }}>PRESCRIPTION HISTORY</p>
        <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
          Past Analyses
        </h1>
        <p className="text-sm" style={{ color: 'hsl(var(--muted-foreground))' }}>
          {total > 0 ? `${total} prescription${total !== 1 ? 's' : ''} on record` : 'No prescriptions yet'}
        </p>
      </div>

      {error && (
        <div
          className="flex items-start gap-3 p-4 rounded-xl border"
          style={{ borderColor: 'rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)' }}
        >
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-400">Failed to load history</p>
            <p className="text-xs mt-1" style={{ color: 'hsl(var(--muted-foreground))' }}>{error}</p>
          </div>
          <button onClick={fetchHistory} className="flex items-center gap-1.5 text-xs text-[#0DCDAA] hover:underline shrink-0">
            <RefreshCw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[1,2,3].map((i) => (
            <div key={i} className="rounded-xl border p-5 space-y-3" style={{ borderColor: 'hsl(var(--border)/0.5)', background: 'hsl(var(--card))' }}>
              <div className="h-4 w-32 rounded skeleton-shimmer" />
              <div className="h-3 w-48 rounded skeleton-shimmer" />
            </div>
          ))}
        </div>
      ) : prescriptions.length === 0 && !error ? (
        <div
          className="py-20 text-center rounded-2xl border"
          style={{ borderColor: 'hsl(var(--border)/0.4)', background: 'hsl(var(--secondary)/0.15)' }}
        >
          <History className="w-10 h-10 mx-auto mb-4" style={{ color: 'hsl(var(--muted-foreground))' }} />
          <p className="text-sm" style={{ color: 'hsl(var(--muted-foreground))' }}>
            No prescriptions uploaded yet.
          </p>
          <Link
            href="/upload"
            className="inline-flex items-center gap-2 mt-5 px-5 py-2.5 rounded-xl font-bold text-sm"
            style={{ background: '#0DCDAA', color: '#071A14' }}
          >
            <UploadCloud className="w-4 h-4" /> Upload First Prescription
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {prescriptions.map((p, i) => (
            <div
              key={p.prescription_id}
              className={cn(
                'rounded-2xl border p-5 space-y-3 rx-hover-glow animate-fade-up opacity-0',
                `stagger-${Math.min(i + 1, 6)}`
              )}
              style={{
                borderColor: 'hsl(var(--border)/0.6)',
                background: 'hsl(var(--card))',
                animationFillMode: 'forwards',
              }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <FileText className="w-4 h-4" style={{ color: '#0DCDAA' }} />
                    <span className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.6rem' }}>
                      {p.prescription_id.split('-')[0].toUpperCase()}…
                    </span>
                    <span
                      className="label-mono px-2 py-0.5 rounded-full border"
                      style={{
                        fontSize: '0.58rem',
                        background: `rgba(13,205,170,${Math.min(p.ocr_confidence, 1) * 0.15})`,
                        borderColor: `rgba(13,205,170,${Math.min(p.ocr_confidence, 1) * 0.3})`,
                        color: '#0DCDAA',
                      }}
                    >
                      {Math.round(p.ocr_confidence * 100)}% OCR
                    </span>
                  </div>

                  {p.detected_medicines.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {p.detected_medicines.map((m) => (
                        <span
                          key={m}
                          className="flex items-center gap-1 label-mono px-2 py-0.5 rounded-md border"
                          style={{
                            fontSize: '0.58rem',
                            background: 'hsl(var(--secondary))',
                            borderColor: 'hsl(var(--border))',
                            color: 'hsl(var(--foreground))',
                          }}
                        >
                          <Pill className="w-2.5 h-2.5" style={{ color: 'hsl(var(--muted-foreground))' }} />
                          {m}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-3 flex-wrap pt-0.5">
                    {p.patient_age && (
                      <span className="flex items-center gap-1 label-mono" style={{ fontSize: '0.58rem', color: 'hsl(var(--muted-foreground))' }}>
                        <User className="w-3 h-3" /> {p.patient_age}y
                      </span>
                    )}
                    {p.doctor_name && (
                      <span className="label-mono" style={{ fontSize: '0.58rem', color: 'hsl(var(--muted-foreground))' }}>
                        Dr. {p.doctor_name}
                      </span>
                    )}
                    <span className="flex items-center gap-1 label-mono" style={{ fontSize: '0.58rem', color: 'hsl(var(--muted-foreground))' }}>
                      <Clock className="w-3 h-3" />
                      {p.detected_medicines.length} medicine{p.detected_medicines.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                <button
                  onClick={() => handleView(p.prescription_id)}
                  disabled={loadingId === p.prescription_id}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl label-mono text-sm shrink-0 transition-all active:scale-95 border disabled:opacity-60"
                  style={{
                    background: '#0DCDAA',
                    color: '#071A14',
                    borderColor: '#0DCDAA',
                    fontSize: '0.65rem',
                  }}
                >
                  {loadingId === p.prescription_id ? (
                    <RefreshCw className="w-3 h-3 animate-spin" />
                  ) : (
                    <ChevronRight className="w-3 h-3" />
                  )}
                  VIEW
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-3 pt-2">
        <Link
          href="/upload"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all active:scale-95"
          style={{ background: '#0DCDAA', color: '#071A14' }}
        >
          <UploadCloud className="w-4 h-4" /> New Analysis
        </Link>
      </div>
    </div>
  )
}
