'use client'

import { cn } from '@/lib/utils'
import type { LifestyleRecommendation } from '@/types/medicine'
import { Ban, CheckCircle2, Heart, Leaf, Info } from 'lucide-react'

interface LifestylePanelProps {
  recommendations: LifestyleRecommendation[]
  medicineName: string
}

const CATEGORY_EMOJI: Record<string, string> = {
  diet:        '🍽️',
  alcohol:     '🚫',
  sunlight:    '☀️',
  driving:     '🚗',
  activity:    '🏃',
  sleep:       '🌙',
  supplement:  '💊',
  smoking:     '🚬',
  caffeine:    '☕',
  other:       '⚠️',
}

const SEVERITY_STYLES = {
  low:      { pill: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20', dot: 'bg-emerald-400' },
  moderate: { pill: 'bg-amber-500/10 text-amber-400 border-amber-500/20',     dot: 'bg-amber-400'   },
  high:     { pill: 'bg-orange-500/10 text-orange-400 border-orange-500/20',   dot: 'bg-orange-400'  },
  critical: { pill: 'bg-red-500/10 text-red-400 border-red-500/20',           dot: 'bg-red-400'     },
}

function RecItem({ rec, index }: { rec: LifestyleRecommendation; index: number }) {
  const sty = SEVERITY_STYLES[rec.severity] ?? SEVERITY_STYLES.moderate
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-xl border p-3.5 animate-fade-up opacity-0 transition-colors',
        rec.severity === 'critical'
          ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/8'
          : rec.severity === 'high'
          ? 'bg-orange-500/5 border-orange-500/20 hover:bg-orange-500/8'
          : 'bg-[hsl(var(--secondary)/0.3)] border-[hsl(var(--border)/0.5)] hover:bg-[hsl(var(--secondary)/0.5)]'
      )}
      style={{ animationDelay: `${index * 0.07}s`, animationFillMode: 'forwards' }}
    >
      <span className="text-lg shrink-0 mt-0.5">{CATEGORY_EMOJI[rec.category] ?? '💊'}</span>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap mb-1">
          <p className="text-sm font-semibold text-[hsl(var(--foreground))]">{rec.title}</p>
          <span className={cn('label-mono px-1.5 py-0.5 rounded-full border text-[0.54rem]', sty.pill)}>
            {rec.severity.toUpperCase()}
          </span>
        </div>
        <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{rec.description}</p>
      </div>
    </div>
  )
}

export default function LifestylePanel({ recommendations, medicineName }: LifestylePanelProps) {
  const avoid       = recommendations.filter((r) => r.section === 'avoid')
  const bestPractice = recommendations.filter((r) => r.section === 'bestPractice')
  const supportive  = recommendations.filter((r) => r.section === 'supportive')

  if (recommendations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
        <Leaf className="w-10 h-10 text-[#0DCDAA]/30" />
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          No specific lifestyle restrictions noted for {medicineName}.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── What to Avoid ─────────────────────────────────────────────── */}
      {avoid.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Ban className="w-3.5 h-3.5 text-red-400" />
            <p className="label-mono text-red-400" style={{ fontSize: '0.62rem' }}>WHAT TO AVOID</p>
          </div>
          <div className="space-y-2">
            {avoid.map((rec, i) => <RecItem key={rec.id} rec={rec} index={i} />)}
          </div>
        </div>
      )}

      {/* ── Best Practices ────────────────────────────────────────────── */}
      {bestPractice.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#0DCDAA]" />
            <p className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.62rem' }}>BEST PRACTICES</p>
          </div>
          <div className="space-y-2">
            {bestPractice.map((rec, i) => <RecItem key={rec.id} rec={rec} index={avoid.length + i} />)}
          </div>
        </div>
      )}

      {/* ── Supportive Lifestyle ──────────────────────────────────────── */}
      {supportive.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Heart className="w-3.5 h-3.5 text-violet-400" />
            <p className="label-mono text-violet-400" style={{ fontSize: '0.62rem' }}>SUPPORTIVE LIFESTYLE</p>
          </div>
          <div className="space-y-2">
            {supportive.map((rec, i) => <RecItem key={rec.id} rec={rec} index={avoid.length + bestPractice.length + i} />)}
          </div>
        </div>
      )}

      {/* ── Disclaimer ───────────────────────────────────────────────── */}
      <div
        className="flex items-start gap-2.5 p-3 rounded-xl border"
        style={{ borderColor: 'rgba(13,205,170,0.12)', background: 'rgba(13,205,170,0.03)' }}
      >
        <Info className="w-3.5 h-3.5 text-[#0DCDAA] shrink-0 mt-0.5" />
        <p className="text-[0.67rem] leading-relaxed text-[hsl(var(--muted-foreground))]">
          These recommendations are AI-generated educational guidance and do not replace the advice of a doctor or pharmacist. Always follow your healthcare professional&apos;s instructions.
        </p>
      </div>
    </div>
  )
}
