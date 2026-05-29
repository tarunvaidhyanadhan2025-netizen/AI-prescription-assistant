'use client'

import { useState } from 'react'
import { cn, getSeverityColor, getFrequencyLabel } from '@/lib/utils'
import type { SideEffect } from '@/types/medicine'
import { ChevronDown, ChevronUp, AlertCircle, Info, Zap, TriangleAlert } from 'lucide-react'

const SEVERITY_ICONS = {
  low: Info,
  moderate: AlertCircle,
  high: TriangleAlert,
  critical: Zap,
}

export default function SideEffectList({
  sideEffects,
  className,
}: {
  sideEffects: SideEffect[]
  className?: string
}) {
  const [expanded, setExpanded] = useState(false)
  const shown = expanded ? sideEffects : sideEffects.slice(0, 3)

  const critCount = sideEffects.filter((s) => s.severity === 'critical').length
  const highCount  = sideEffects.filter((s) => s.severity === 'high').length

  return (
    <div className={cn('space-y-2', className)}>
      {/* Summary */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
          {sideEffects.length} EFFECTS:
        </span>
        {critCount > 0 && (
          <span className="label-mono px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20" style={{ fontSize: '0.58rem' }}>
            {critCount} CRITICAL
          </span>
        )}
        {highCount > 0 && (
          <span className="label-mono px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-400 border border-orange-500/20" style={{ fontSize: '0.58rem' }}>
            {highCount} HIGH
          </span>
        )}
      </div>

      {/* List */}
      <div className="space-y-1.5">
        {shown.map((effect, i) => {
          const colors = getSeverityColor(effect.severity)
          const Icon   = SEVERITY_ICONS[effect.severity]
          return (
            <div
              key={effect.id}
              className={cn(
                'rounded-xl border p-3 bg-[hsl(var(--card))] animate-fade-up opacity-0',
                colors.border,
                `stagger-${Math.min(i + 1, 6)}`
              )}
              style={{ animationFillMode: 'forwards' }}
            >
              <div className="flex items-start gap-3">
                <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border', colors.bg, colors.border)}>
                  <Icon className={cn('w-3.5 h-3.5', colors.text)} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-sm font-medium text-[hsl(var(--foreground))]">{effect.name}</p>
                    <span className={cn('label-mono px-1.5 py-0.5 rounded-full', colors.badge)} style={{ fontSize: '0.58rem' }}>
                      {effect.severity.toUpperCase()}
                    </span>
                    <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
                      {getFrequencyLabel(effect.frequency)}
                    </span>
                  </div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1 leading-relaxed">{effect.description}</p>
                  {effect.actionRequired && (
                    <div className={cn('flex items-start gap-1.5 mt-2 p-2 rounded-lg border', colors.bg, colors.border)}>
                      <AlertCircle className={cn('w-3 h-3 mt-0.5 shrink-0', colors.text)} />
                      <p className={cn('text-xs', colors.text)}>{effect.actionRequired}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {sideEffects.length > 3 && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-[hsl(var(--border)/0.6)] text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:border-[#0DCDAA]/30 hover:bg-[#0DCDAA]/3 transition-all"
        >
          {expanded ? (
            <><ChevronUp className="w-3.5 h-3.5" /> Show less</>
          ) : (
            <><ChevronDown className="w-3.5 h-3.5" /> Show {sideEffects.length - 3} more</>
          )}
        </button>
      )}
    </div>
  )
}
