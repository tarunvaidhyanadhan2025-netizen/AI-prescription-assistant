'use client'

import { cn, getDrowsinessConfig } from '@/lib/utils'
import type { DrowsinessLevel } from '@/types/medicine'
import { Moon, Car, AlertTriangle, CheckCircle } from 'lucide-react'

interface DrowsinessIndicatorProps {
  level: DrowsinessLevel
  medicineName: string
  compact?: boolean
  className?: string
}

const ICONS = { none: CheckCircle, mild: Moon, moderate: Car, severe: AlertTriangle }
const BARS  = { none: 0, mild: 1, moderate: 2, severe: 3 }

const BORDER_MAP = {
  none:     'border-emerald-500/20',
  mild:     'border-amber-500/20',
  moderate: 'border-orange-500/20',
  severe:   'border-red-500/30',
}

const BAR_COLOR = {
  none:     'bg-emerald-400',
  mild:     'bg-amber-400',
  moderate: 'bg-orange-400',
  severe:   'bg-red-400',
}

export default function DrowsinessIndicator({
  level,
  medicineName,
  compact = false,
  className,
}: DrowsinessIndicatorProps) {
  const config = getDrowsinessConfig(level)
  const Icon  = ICONS[level]
  const bars  = BARS[level]

  if (compact) {
    return (
      <span
        className={cn(
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border',
          config.bgColor,
          BORDER_MAP[level],
          level === 'severe' && 'warning-pulse',
          className
        )}
      >
        <Icon className={cn('w-3 h-3', config.color)} />
        <span className={cn('label-mono', config.color)} style={{ fontSize: '0.58rem' }}>
          {config.label.toUpperCase()}
        </span>
      </span>
    )
  }

  return (
    <div
      className={cn(
        'rounded-xl border p-4 space-y-3',
        config.bgColor,
        BORDER_MAP[level],
        level === 'severe' && 'warning-pulse',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center border', config.bgColor, BORDER_MAP[level])}>
            <Icon className={cn('w-[18px] h-[18px]', config.color)} />
          </div>
          <div>
            <p className={cn('text-sm font-semibold', config.color)}>{config.label}</p>
            <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>DROWSINESS RISK</p>
          </div>
        </div>
        {/* Mini bar chart */}
        <div className="flex items-end gap-0.5 h-6">
          {[1, 2, 3].map((b) => (
            <div
              key={b}
              className={cn('w-2 rounded-sm', b <= bars ? BAR_COLOR[level] : 'bg-[hsl(var(--secondary))]')}
              style={{ height: `${b * 32}%` }}
            />
          ))}
        </div>
      </div>

      <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{config.description}</p>

      {level === 'severe' && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-red-500/10 border border-red-500/20">
          <Car className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
          <p className="text-xs text-red-300">
            <strong>Do NOT</strong> drive or operate heavy machinery while taking {medicineName}.
          </p>
        </div>
      )}
      {level === 'moderate' && (
        <div className="flex items-start gap-2 p-2.5 rounded-lg bg-orange-500/10 border border-orange-500/20">
          <Car className="w-3.5 h-3.5 text-orange-400 mt-0.5 shrink-0" />
          <p className="text-xs text-orange-300">
            Avoid driving until you understand your individual response to {medicineName}.
          </p>
        </div>
      )}
    </div>
  )
}
