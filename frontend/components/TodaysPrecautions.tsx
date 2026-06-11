'use client'

import { cn } from '@/lib/utils'
import type { TodayPrecaution } from '@/types/medicine'
import { ShieldCheck, Info } from 'lucide-react'

interface TodaysPrecautionsProps {
  precautions: TodayPrecaution[]
}

const SEVERITY_BORDER: Record<string, string> = {
  low:      'border-emerald-500/20 bg-emerald-500/5',
  moderate: 'border-amber-500/20 bg-amber-500/5',
  high:     'border-orange-500/20 bg-orange-500/5',
  critical: 'border-red-500/20 bg-red-500/5',
}

const SEVERITY_TEXT: Record<string, string> = {
  low:      'text-emerald-300',
  moderate: 'text-amber-300',
  high:     'text-orange-300',
  critical: 'text-red-300',
}

export default function TodaysPrecautions({ precautions }: TodaysPrecautionsProps) {
  if (!precautions || precautions.length === 0) return null

  // Sort: critical first, then high, then moderate, then low
  const SEVERITY_RANK: Record<string, number> = { critical: 0, high: 1, moderate: 2, low: 3 }
  const sorted = [...precautions].sort(
    (a, b) => (SEVERITY_RANK[a.severity] ?? 4) - (SEVERITY_RANK[b.severity] ?? 4)
  )

  return (
    <div
      className="rounded-2xl border overflow-hidden animate-fade-up opacity-0"
      style={{
        borderColor: 'rgba(13,205,170,0.2)',
        background: 'hsl(var(--card))',
        animationFillMode: 'forwards',
        animationDelay: '0.15s',
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-3.5 border-b flex items-center gap-2.5"
        style={{ borderColor: 'rgba(13,205,170,0.15)', background: 'rgba(13,205,170,0.06)' }}
      >
        <ShieldCheck className="w-4 h-4 text-[#0DCDAA]" />
        <div>
          <p className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.62rem' }}>TODAY&apos;S PRECAUTIONS</p>
          <p className="text-[0.67rem] text-[hsl(var(--muted-foreground))]">
            Key actions for your current prescription — read before taking today&apos;s dose
          </p>
        </div>
      </div>

      {/* Grid of precautions */}
      <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sorted.map((p, i) => (
          <div
            key={p.id}
            className={cn(
              'flex items-start gap-3 rounded-xl border px-3.5 py-3 animate-fade-up opacity-0',
              SEVERITY_BORDER[p.severity] ?? SEVERITY_BORDER.moderate
            )}
            style={{ animationDelay: `${0.15 + i * 0.06}s`, animationFillMode: 'forwards' }}
          >
            <span className="text-lg leading-none shrink-0 mt-0.5">{p.emoji}</span>
            <p className={cn('text-xs font-medium leading-relaxed', SEVERITY_TEXT[p.severity] ?? SEVERITY_TEXT.moderate)}>
              {p.text}
            </p>
          </div>
        ))}
      </div>

      {/* Disclaimer footer */}
      <div
        className="px-5 py-3 border-t flex items-start gap-2"
        style={{ borderColor: 'rgba(13,205,170,0.1)', background: 'rgba(13,205,170,0.02)' }}
      >
        <Info className="w-3 h-3 text-[hsl(var(--muted-foreground))] shrink-0 mt-0.5" />
        <p className="text-[0.62rem] text-[hsl(var(--muted-foreground))] leading-relaxed">
          These recommendations are AI-generated educational guidance and do not replace the advice of a doctor or pharmacist. Always follow your healthcare professional&apos;s instructions.
        </p>
      </div>
    </div>
  )
}
