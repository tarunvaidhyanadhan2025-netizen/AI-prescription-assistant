'use client'

import { cn, getSeverityColor } from '@/lib/utils'
import type { DrugInteraction, AgeWarning, SeverityLevel } from '@/types/medicine'
import { AlertTriangle, Skull, Info, Users } from 'lucide-react'

interface WarningCardProps {
  type?: 'interaction' | 'age' | 'alert' | 'general'
  title: string
  description: string
  severity?: SeverityLevel
  recommendation?: string
  badge?: string
  className?: string
}

export function WarningCard({
  title,
  description,
  severity = 'moderate',
  recommendation,
  badge,
  className,
}: WarningCardProps) {
  const colors = getSeverityColor(severity)
  const Icon = severity === 'critical' ? Skull : severity === 'high' ? AlertTriangle : Info

  return (
    <div
      className={cn(
        'rounded-xl border p-4 space-y-2.5',
        colors.bg,
        colors.border,
        severity === 'critical' && 'warning-pulse',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center border shrink-0', colors.bg, colors.border)}>
          <Icon className={cn('w-4 h-4', colors.text)} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className={cn('text-sm font-semibold', colors.text)}>{title}</p>
            {badge && (
              <span className={cn('label-mono px-1.5 py-0.5 rounded-full border', colors.badge, colors.border)} style={{ fontSize: '0.58rem' }}>
                {badge}
              </span>
            )}
          </div>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 leading-relaxed">{description}</p>
        </div>
      </div>
      {recommendation && (
        <div className="ml-11 flex items-start gap-2 p-2.5 rounded-lg bg-[hsl(var(--background)/0.6)] border border-[hsl(var(--border)/0.4)]">
          <span className="label-mono text-[hsl(var(--muted-foreground))] shrink-0 mt-0.5" style={{ fontSize: '0.58rem' }}>REC:</span>
          <p className="text-xs text-[hsl(var(--foreground))] leading-relaxed">{recommendation}</p>
        </div>
      )}
    </div>
  )
}

// ─── Interactions panel ───────────────────────────────────────────────────────
export function InteractionsPanel({ interactions, className }: { interactions: DrugInteraction[]; className?: string }) {
  if (!interactions.length) return null
  return (
    <div className={cn('space-y-2', className)}>
      <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
        {interactions.length} DRUG INTERACTION{interactions.length !== 1 ? 'S' : ''}
      </p>
      {interactions.map((it) => (
        <WarningCard
          key={it.id}
          title={`+ ${it.drugName}`}
          description={it.description}
          severity={it.severity}
          recommendation={it.recommendation}
          badge={it.severity.toUpperCase()}
        />
      ))}
    </div>
  )
}

// ─── Age warnings panel ───────────────────────────────────────────────────────
const AGE_LABELS: Record<string, string> = {
  pediatric: 'Children (<18 yrs)',
  adult:     'Adults',
  geriatric: 'Elderly (>65 yrs)',
  all:       'All Ages',
}

export function AgeWarningsPanel({
  warnings,
  patientAge,
  className,
}: {
  warnings: AgeWarning[]
  patientAge?: number
  className?: string
}) {
  if (!warnings.length) return null
  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex items-center gap-2">
        <Users className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))]" />
        <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
          AGE-SPECIFIC WARNINGS{patientAge ? ` — PATIENT AGE: ${patientAge}Y` : ''}
        </p>
      </div>
      {warnings.map((w, i) => (
        <div
          key={i}
          className={cn(
            'rounded-xl border p-3.5 space-y-1.5',
            w.contraindicated
              ? 'border-red-500/30 bg-red-500/5'
              : 'border-amber-500/20 bg-amber-500/5'
          )}
        >
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={cn(
                'label-mono px-2 py-0.5 rounded-full border',
                w.contraindicated
                  ? 'bg-red-500/15 text-red-400 border-red-500/20'
                  : 'bg-amber-500/15 text-amber-400 border-amber-500/20'
              )}
              style={{ fontSize: '0.58rem' }}
            >
              {AGE_LABELS[w.ageGroup] || w.ageGroup}
            </span>
            {w.contraindicated && (
              <span className="label-mono px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20" style={{ fontSize: '0.58rem' }}>
                CONTRAINDICATED
              </span>
            )}
          </div>
          <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{w.warning}</p>
          {w.adjustedDose && (
            <div className="flex items-start gap-1.5 pt-0.5">
              <span className="label-mono text-[#0DCDAA] shrink-0" style={{ fontSize: '0.58rem' }}>DOSE ADJ:</span>
              <p className="text-xs text-[#0DCDAA]/80">{w.adjustedDose}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
