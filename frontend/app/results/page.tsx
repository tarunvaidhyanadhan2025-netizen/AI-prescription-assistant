'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import MedicineCard from '@/components/MedicineCard'
import { WarningCard } from '@/components/WarningCard'
import { SkeletonCard } from '@/components/LoadingState'
import {
  cn,
  formatTimestamp,
  getConfidenceLabel,
  getConfidenceColor,
} from '@/lib/utils'
import type { PrescriptionAnalysis } from '@/types/medicine'
import { mockAnalyzePrescription } from '@/services/api'
import {
  Download,
  RefreshCw,
  UploadCloud,
  Activity,
  AlertTriangle,
  ShieldAlert,
  FileText,
  ChevronDown,
  Printer,
} from 'lucide-react'

type Filter = 'all' | 'critical' | 'warnings'

export default function ResultsPage() {
  const [analysis, setAnalysis] = useState<PrescriptionAnalysis | null>(null)
  const [loading, setLoading]   = useState(true)
  const [showRaw, setShowRaw]   = useState(false)
  const [filter, setFilter]     = useState<Filter>('all')

  useEffect(() => {
    mockAnalyzePrescription({}).then((res) => {
      if (res.success && res.data) setAnalysis(res.data)
      setLoading(false)
    })
  }, [])

  /* ── Loading skeleton ─────────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10">
        <div className="mb-8 space-y-2">
          <div className="h-3 w-20 rounded skeleton-shimmer" />
          <div className="h-8 w-64 rounded skeleton-shimmer" />
          <div className="h-3 w-44 rounded skeleton-shimmer" />
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[1,2,3,4].map((i) => (
            <div key={i} className="rounded-xl border p-4 space-y-2" style={{ borderColor: 'hsl(var(--border)/0.5)', background: 'hsl(var(--card))' }}>
              <div className="h-4 w-4 rounded skeleton-shimmer" />
              <div className="h-7 w-8 rounded skeleton-shimmer" />
              <div className="h-3 w-16 rounded skeleton-shimmer" />
            </div>
          ))}
        </div>
        <div className="space-y-4">
          {[1,2,3].map((i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    )
  }

  /* ── Empty state ──────────────────────────────────────────────────────── */
  if (!analysis) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-20 text-center space-y-5">
        <div
          className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto border"
          style={{ background: 'hsl(var(--secondary))', borderColor: 'hsl(var(--border))' }}
        >
          <FileText className="w-7 h-7" style={{ color: 'hsl(var(--muted-foreground))' }} />
        </div>
        <h2 className="text-xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>No Analysis Found</h2>
        <p className="text-sm" style={{ color: 'hsl(var(--muted-foreground))' }}>
          Upload a prescription first to see your safety report here.
        </p>
        <Link
          href="/upload"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all active:scale-95"
          style={{ background: '#0DCDAA', color: '#071A14' }}
        >
          <UploadCloud className="w-4 h-4" />
          Upload Prescription
        </Link>
      </div>
    )
  }

  /* ── Derived data ────────────────────────────────────────────────────── */
  const totalSideEffects  = analysis.extractedMedicines.flatMap((m) => m.sideEffects).length
  const totalInteractions = analysis.extractedMedicines.flatMap((m) => m.interactions).length

  const filteredMeds = analysis.extractedMedicines.filter((m) => {
    if (filter === 'critical') {
      return (
        m.sideEffects.some((s) => s.severity === 'critical') ||
        m.interactions.some((i) => i.severity === 'critical') ||
        m.drowsinessLevel === 'severe'
      )
    }
    if (filter === 'warnings') {
      return m.ageWarnings.length > 0 || m.drowsinessLevel !== 'none'
    }
    return true
  })

  /* ── Main render ─────────────────────────────────────────────────────── */
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">

      {/* ── Page header ─────────────────────────────────────────────────── */}
      <div className="space-y-1.5">
        <p className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.62rem' }}>ANALYSIS COMPLETE</p>
        <h1 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
          Prescription Safety Report
        </h1>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="label-mono" style={{ fontSize: '0.6rem', color: 'hsl(var(--muted-foreground))' }}>
            {formatTimestamp(analysis.analysisTimestamp)}
          </span>
          <span style={{ color: 'hsl(var(--border))' }}>·</span>
          <span className={cn('label-mono', getConfidenceColor(analysis.confidence))} style={{ fontSize: '0.6rem' }}>
            {getConfidenceLabel(analysis.confidence)} CONFIDENCE ({Math.round(analysis.confidence * 100)}%)
          </span>
          {analysis.patientAge && (
            <>
              <span style={{ color: 'hsl(var(--border))' }}>·</span>
              <span className="label-mono" style={{ fontSize: '0.6rem', color: 'hsl(var(--muted-foreground))' }}>
                PATIENT AGE: {analysis.patientAge}Y
              </span>
            </>
          )}
        </div>
      </div>

      {/* ── Stats overview ──────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { value: analysis.extractedMedicines.length, label: 'Medicines',      color: '#0DCDAA',  Icon: Activity        },
          { value: totalSideEffects,                    label: 'Side Effects',   color: '#F59E0B',  Icon: AlertTriangle   },
          { value: totalInteractions,                   label: 'Interactions',   color: '#F97316',  Icon: ShieldAlert     },
          { value: analysis.criticalAlerts.length,      label: 'Critical Alerts',color: '#EF4444',  Icon: AlertTriangle   },
        ].map(({ value, label, color, Icon }, i) => (
          <div
            key={label}
            className={cn('rounded-xl border p-4 space-y-2 animate-fade-up opacity-0', `stagger-${i + 1}`)}
            style={{
              borderColor: 'hsl(var(--border)/0.6)',
              background: 'hsl(var(--card))',
              animationFillMode: 'forwards',
            }}
          >
            <Icon className="w-4 h-4" style={{ color }} />
            <p className="text-2xl font-extrabold font-mono" style={{ color }}>{value}</p>
            <p className="label-mono" style={{ fontSize: '0.58rem', color: 'hsl(var(--muted-foreground))' }}>
              {label.toUpperCase()}
            </p>
          </div>
        ))}
      </div>

      {/* ── Critical alerts ─────────────────────────────────────────────── */}
      {analysis.criticalAlerts.length > 0 && (
        <div className="space-y-2 animate-fade-in">
          <p className="label-mono text-red-400" style={{ fontSize: '0.62rem' }}>
            ⚠ CRITICAL ALERTS — READ BEFORE TAKING MEDICATION
          </p>
          {analysis.criticalAlerts.map((alert, i) => (
            <WarningCard
              key={i}
              title="Critical Safety Alert"
              description={alert}
              severity="critical"
            />
          ))}
        </div>
      )}

      {/* ── General warnings ────────────────────────────────────────────── */}
      {analysis.overallWarnings.length > 0 && (
        <div className="space-y-2">
          <p className="label-mono text-amber-400" style={{ fontSize: '0.62rem' }}>GENERAL WARNINGS</p>
          {analysis.overallWarnings.map((warn, i) => (
            <WarningCard
              key={i}
              title="Prescription Warning"
              description={warn}
              severity="moderate"
            />
          ))}
        </div>
      )}

      {/* ── Filter + actions bar ────────────────────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="label-mono" style={{ fontSize: '0.58rem', color: 'hsl(var(--muted-foreground))' }}>FILTER:</span>
        {([
          { id: 'all'      as Filter, label: `All (${analysis.extractedMedicines.length})` },
          { id: 'critical' as Filter, label: 'Critical Only' },
          { id: 'warnings' as Filter, label: 'With Warnings'  },
        ]).map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setFilter(id)}
            className={cn('label-mono px-3 py-1.5 rounded-lg border transition-colors')}
            style={{
              fontSize: '0.6rem',
              background: filter === id ? 'rgba(13,205,170,0.1)'        : 'hsl(var(--secondary))',
              borderColor: filter === id ? 'rgba(13,205,170,0.3)'        : 'hsl(var(--border)/0.6)',
              color:       filter === id ? '#0DCDAA'                     : 'hsl(var(--muted-foreground))',
            }}
          >
            {label.toUpperCase()}
          </button>
        ))}

        {/* Spacer + right actions */}
        <div className="ml-auto flex items-center gap-2">
          <button
            onClick={() => setShowRaw((s) => !s)}
            className="flex items-center gap-1.5 label-mono px-3 py-1.5 rounded-lg border transition-colors"
            style={{ fontSize: '0.6rem', borderColor: 'hsl(var(--border)/0.6)', color: 'hsl(var(--muted-foreground))' }}
          >
            <FileText className="w-3 h-3" />
            RAW TEXT
            <ChevronDown className={cn('w-3 h-3 transition-transform', showRaw && 'rotate-180')} />
          </button>

          <Link
            href="/upload"
            className="flex items-center gap-1.5 label-mono px-3 py-1.5 rounded-lg border transition-colors"
            style={{ fontSize: '0.6rem', borderColor: 'hsl(var(--border)/0.6)', color: 'hsl(var(--muted-foreground))' }}
          >
            <RefreshCw className="w-3 h-3" /> NEW
          </Link>
        </div>
      </div>

      {/* ── Raw OCR text ────────────────────────────────────────────────── */}
      {showRaw && (
        <div
          className="rounded-xl border p-4 animate-fade-in"
          style={{ borderColor: 'hsl(var(--border)/0.5)', background: '#0D0F14' }}
        >
          <p className="label-mono text-[#0DCDAA] mb-2" style={{ fontSize: '0.6rem' }}>EXTRACTED TEXT (OCR)</p>
          <pre className="text-xs font-mono leading-relaxed whitespace-pre-wrap overflow-auto" style={{ color: 'rgba(13,205,170,0.7)' }}>
            {analysis.rawText}
          </pre>
        </div>
      )}

      {/* ── Medicine cards ──────────────────────────────────────────────── */}
      <div className="space-y-4">
        <p className="label-mono" style={{ fontSize: '0.6rem', color: 'hsl(var(--muted-foreground))' }}>
          {filteredMeds.length} MEDICINE{filteredMeds.length !== 1 ? 'S' : ''} FOUND
        </p>

        {filteredMeds.length === 0 ? (
          <div
            className="py-12 text-center rounded-2xl border"
            style={{ borderColor: 'hsl(var(--border)/0.4)', background: 'hsl(var(--secondary)/0.15)' }}
          >
            <p className="text-sm" style={{ color: 'hsl(var(--muted-foreground))' }}>
              No medicines match this filter.
            </p>
          </div>
        ) : (
          filteredMeds.map((med, i) => (
            <MedicineCard
              key={med.id}
              medicine={med}
              index={i}
              patientAge={analysis.patientAge}
            />
          ))
        )}
      </div>

      {/* ── Medical disclaimer ──────────────────────────────────────────── */}
      <div
        className="flex items-start gap-3 p-4 rounded-xl border"
        style={{ borderColor: 'rgba(245,158,11,0.2)', background: 'rgba(245,158,11,0.04)' }}
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <p className="text-xs leading-relaxed" style={{ color: 'hsl(var(--muted-foreground))' }}>
          <strong className="text-amber-400">Medical Disclaimer: </strong>
          This analysis is generated by AI for informational purposes only and does not constitute medical advice. Always consult your doctor or pharmacist before making any changes to your medication regimen.
        </p>
      </div>

      {/* ── Action buttons ──────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 pb-4">
        <button
          onClick={() => window.print()}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all border"
          style={{ background: 'hsl(var(--secondary))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
        >
          <Printer className="w-4 h-4" style={{ color: 'hsl(var(--muted-foreground))' }} />
          Print Report
        </button>
        <button
          onClick={() => {
            const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' })
            const url  = URL.createObjectURL(blob)
            const a    = document.createElement('a')
            a.href     = url
            a.download = `rx-report-${analysis.id}.json`
            a.click()
            URL.revokeObjectURL(url)
          }}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all border"
          style={{ background: 'hsl(var(--secondary))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
        >
          <Download className="w-4 h-4" style={{ color: 'hsl(var(--muted-foreground))' }} />
          Download JSON
        </button>
        <Link
          href="/upload"
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all active:scale-95"
          style={{ background: '#0DCDAA', color: '#071A14', boxShadow: '0 0 20px rgba(13,205,170,0.2)' }}
        >
          <UploadCloud className="w-4 h-4" />
          Analyse Another
        </Link>
      </div>
    </div>
  )
}
