'use client'

import { useState } from 'react'
import { cn, getSeverityColor, getFrequencyLabel } from '@/lib/utils'
import type { SideEffect } from '@/types/medicine'
import { ChevronDown, ChevronUp, AlertCircle, Info, TriangleAlert, ShieldAlert } from 'lucide-react'

// Icon per severity — critical uses ShieldAlert (not Zap) to feel informative not scary
const SEVERITY_ICONS = {
  low:      Info,
  moderate: AlertCircle,
  high:     TriangleAlert,
  critical: ShieldAlert,
}

// Human-readable severity labels that convey advisory intent, not alarm
const SEVERITY_LABELS: Record<string, string> = {
  low:      'Common',
  moderate: 'Moderate',
  high:     'Notable',
  critical: 'Rare — Seek Help',
}

export default function SideEffectList({
  sideEffects,
  className,
}: {
  sideEffects: SideEffect[]
  className?: string
}) {
  const [expanded, setExpanded] = useState(false)

  // Sort: critical first so they're immediately visible without expanding
  const sorted = [...sideEffects].sort((a, b) => {
    const order = { critical: 0, high: 1, moderate: 2, low: 3 }
    return (order[a.severity] ?? 4) - (order[b.severity] ?? 4)
  })
  const shown = expanded ? sorted : sorted.slice(0, 4)

  const critCount = sideEffects.filter((s) => s.severity === 'critical').length
  const highCount  = sideEffects.filter((s) => s.severity === 'high').length

  return (
    <div className={cn('space-y-3', className)}>

      {/* Contextual header — advisory framing */}
      <div className="rounded-xl border border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.15)] p-3 space-y-1">
        <p className="text-xs font-medium text-[hsl(var(--foreground))]">
          About these side effects
        </p>
        <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">
          Side effects listed here are <em>possible</em> reactions documented for this medicine class. Most patients experience none or only mild effects. Rare effects are listed so you know when to seek help — not because they are likely.
        </p>
      </div>

      {/* Summary counts */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
          {sideEffects.length} DOCUMENTED EFFECT{sideEffects.length !== 1 ? 'S' : ''}:
        </span>
        {critCount > 0 && (
          <span className="label-mono px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 border border-red-500/20" style={{ fontSize: '0.58rem' }}>
            {critCount} RARE / SEEK HELP
          </span>
        )}
        {highCount > 0 && (
          <span className="label-mono px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400 border border-orange-500/20" style={{ fontSize: '0.58rem' }}>
            {highCount} NOTABLE
          </span>
        )}
      </div>

      {/* Effect list */}
      <div className="space-y-2">
        {shown.map((effect, i) => {
          const colors = getSeverityColor(effect.severity)
          const Icon   = SEVERITY_ICONS[effect.severity]
          const isCritical = effect.severity === 'critical'

          return (
            <div
              key={effect.id}
              className={cn(
                'rounded-xl border p-3 animate-fade-up opacity-0',
                // Critical: slightly more prominent background, but NOT a pulsing red alarm
                isCritical
                  ? 'bg-red-500/5 border-red-500/25'
                  : cn('bg-[hsl(var(--card))]', colors.border),
              )}
              style={{ animationFillMode: 'forwards', animationDelay: `${i * 0.05}s` }}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={cn(
                  'w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border',
                  colors.bg, colors.border
                )}>
                  <Icon className={cn('w-3.5 h-3.5', colors.text)} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium text-[hsl(var(--foreground))]">{effect.name}</p>
                    {/* Severity badge — uses advisory label, not raw "CRITICAL" */}
                    <span className={cn('label-mono px-1.5 py-0.5 rounded-full border', colors.badge, colors.border)} style={{ fontSize: '0.56rem' }}>
                      {SEVERITY_LABELS[effect.severity] ?? effect.severity.toUpperCase()}
                    </span>
                    <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.56rem' }}>
                      {getFrequencyLabel(effect.frequency)}
                    </span>
                  </div>

                  {effect.description && effect.description !== effect.name && (
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 leading-relaxed">{effect.description}</p>
                  )}

                  {/* Action required — styled as calm advisory, not alarm */}
                  {effect.actionRequired && (
                    <div className={cn(
                      'flex items-start gap-1.5 mt-2 p-2 rounded-lg border',
                      isCritical ? 'bg-red-500/5 border-red-500/20' : cn(colors.bg, colors.border)
                    )}>
                      <Info className={cn('w-3 h-3 mt-0.5 shrink-0', colors.text)} />
                      <p className={cn('text-xs', colors.text)}>{effect.actionRequired}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {sideEffects.length > 4 && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-[hsl(var(--border)/0.6)] text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:border-[#0DCDAA]/30 hover:bg-[#0DCDAA]/3 transition-all"
        >
          {expanded ? (
            <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
          ) : (
            <><ChevronDown className="w-3.5 h-3.5" /> Show {sideEffects.length - 4} more effects</>
          )}
        </button>
      )}
    </div>
  )
}
