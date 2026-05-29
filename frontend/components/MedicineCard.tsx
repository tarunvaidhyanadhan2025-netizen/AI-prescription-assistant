'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { Medicine } from '@/types/medicine'
import DrowsinessIndicator from './DrowsinessIndicator'
import SideEffectList from './SideEffectList'
import DosageSafetyCard from './DosageSafetyCard'
import { InteractionsPanel, AgeWarningsPanel } from './WarningCard'
import { ChevronDown, ChevronUp, FlaskConical, ShieldAlert, Leaf, Lock, Pill } from 'lucide-react'

interface MedicineCardProps {
  medicine: Medicine
  index: number
  patientAge?: number
  className?: string
}

type Tab = 'overview' | 'dosage' | 'sideEffects' | 'interactions' | 'lifestyle'
const TABS: { id: Tab; label: string }[] = [
  { id: 'overview',      label: 'Overview' },
  { id: 'dosage',        label: 'Dosage' },
  { id: 'sideEffects',   label: 'Side Effects' },
  { id: 'interactions',  label: 'Interactions' },
  { id: 'lifestyle',     label: 'Lifestyle' },
]

const LIFESTYLE_EMOJI: Record<string, string> = {
  diet: '🥗', activity: '🏃', alcohol: '🚫',
  sunlight: '☀️', sleep: '🌙', driving: '🚗', other: '💊',
}

const LIFESTYLE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  low:      { bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400' },
  moderate: { bg: 'bg-amber-500/10',   border: 'border-amber-500/20',   text: 'text-amber-400'   },
  high:     { bg: 'bg-orange-500/10',  border: 'border-orange-500/20',  text: 'text-orange-400'  },
  critical: { bg: 'bg-red-500/10',     border: 'border-red-500/20',     text: 'text-red-400'     },
}

export default function MedicineCard({ medicine, index, patientAge, className }: MedicineCardProps) {
  const [tab, setTab]           = useState<Tab>('overview')
  const [collapsed, setCollapsed] = useState(false)

  const hasCriticalEffect      = medicine.sideEffects.some((s) => s.severity === 'critical')
  const hasCriticalInteraction = medicine.interactions.some((i) => i.severity === 'critical')
  const anyCritical            = hasCriticalEffect || hasCriticalInteraction || medicine.drowsinessLevel === 'severe'

  return (
    <div
      className={cn(
        'rounded-2xl border border-[hsl(var(--border)/0.6)] bg-[hsl(var(--card))] overflow-hidden rx-hover-glow',
        'animate-fade-up opacity-0',
        className
      )}
      style={{ animationDelay: `${index * 0.1}s`, animationFillMode: 'forwards' }}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.2)]">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            {/* Index badge */}
            <div className="w-8 h-8 rounded-lg bg-[#0DCDAA]/15 border border-[#0DCDAA]/25 flex items-center justify-center shrink-0">
              <span className="font-mono text-[#0DCDAA] font-bold text-sm">{index + 1}</span>
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-base font-bold text-[hsl(var(--foreground))]">{medicine.name}</h3>
                {medicine.controlledSubstance && (
                  <span className="flex items-center gap-1 label-mono px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20" style={{ fontSize: '0.58rem' }}>
                    <Lock style={{ width: 9, height: 9 }} /> CONTROLLED
                  </span>
                )}
                {anyCritical && (
                  <span className="label-mono px-2 py-0.5 rounded-full bg-red-500/15 text-red-400 border border-red-500/20 warning-pulse" style={{ fontSize: '0.58rem' }}>
                    ⚠ CRITICAL
                  </span>
                )}
              </div>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 font-mono">{medicine.genericName}</p>
              <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                <span className="label-mono px-2 py-0.5 rounded-full bg-[#3A7FD4]/10 text-[#3A7FD4] border border-[#3A7FD4]/20" style={{ fontSize: '0.58rem' }}>
                  {medicine.drugClass}
                </span>
                <span className="label-mono px-2 py-0.5 rounded-full bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
                  {medicine.indication}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <DrowsinessIndicator level={medicine.drowsinessLevel} medicineName={medicine.name} compact />
            <button
              onClick={() => setCollapsed((c) => !c)}
              className="p-1.5 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors"
              aria-label={collapsed ? 'Expand card' : 'Collapse card'}
            >
              {collapsed ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {!collapsed && (
        <>
          {/* Tab bar */}
          <div className="flex overflow-x-auto border-b border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.1)] scrollbar-hide">
            {TABS.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={cn(
                  'px-4 py-2.5 label-mono shrink-0 transition-colors border-b-2',
                  tab === id
                    ? 'border-[#0DCDAA] text-[#0DCDAA] bg-[#0DCDAA]/5'
                    : 'border-transparent text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                )}
                style={{ fontSize: '0.62rem' }}
              >
                {label.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="p-5">
            {/* OVERVIEW */}
            {tab === 'overview' && (
              <div className="space-y-4 animate-fade-in">
                <div>
                  <p className="label-mono text-[hsl(var(--muted-foreground))] mb-1.5" style={{ fontSize: '0.58rem' }}>DESCRIPTION</p>
                  <p className="text-sm text-[hsl(var(--foreground))] leading-relaxed">{medicine.description}</p>
                </div>

                <div className="rounded-xl border border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.2)] p-3.5">
                  <div className="flex items-center gap-1.5 mb-2">
                    <FlaskConical className="w-3.5 h-3.5 text-[#3A7FD4]" />
                    <p className="label-mono text-[#3A7FD4]" style={{ fontSize: '0.58rem' }}>MECHANISM OF ACTION</p>
                  </div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{medicine.mechanism}</p>
                </div>

                <div className="flex gap-4 flex-wrap">
                  <div className="flex-1 min-w-[140px]">
                    <p className="label-mono text-[hsl(var(--muted-foreground))] mb-1.5" style={{ fontSize: '0.58rem' }}>BRAND NAMES</p>
                    <div className="flex flex-wrap gap-1.5">
                      {medicine.brandNames.map((b) => (
                        <span key={b} className="label-mono px-2 py-0.5 rounded-lg bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--foreground))]" style={{ fontSize: '0.58rem' }}>
                          {b}
                        </span>
                      ))}
                    </div>
                  </div>
                  {medicine.pregnancyCategory && (
                    <div>
                      <p className="label-mono text-[hsl(var(--muted-foreground))] mb-1.5" style={{ fontSize: '0.58rem' }}>PREGNANCY</p>
                      <span className="label-mono px-2 py-1 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20" style={{ fontSize: '0.58rem' }}>
                        CATEGORY {medicine.pregnancyCategory}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex items-start gap-2 p-2.5 rounded-lg border border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.2)]">
                  <Pill className="w-3.5 h-3.5 text-[hsl(var(--muted-foreground))] mt-0.5 shrink-0" />
                  <div>
                    <p className="label-mono text-[hsl(var(--muted-foreground))] mb-0.5" style={{ fontSize: '0.58rem' }}>STORAGE</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{medicine.storageInstructions}</p>
                  </div>
                </div>

                <DrowsinessIndicator level={medicine.drowsinessLevel} medicineName={medicine.name} />
              </div>
            )}

            {/* DOSAGE */}
            {tab === 'dosage' && (
              <div className="animate-fade-in">
                <DosageSafetyCard dosage={medicine.dosage} medicineName={medicine.name} />
              </div>
            )}

            {/* SIDE EFFECTS */}
            {tab === 'sideEffects' && (
              <div className="animate-fade-in">
                <SideEffectList sideEffects={medicine.sideEffects} />
              </div>
            )}

            {/* INTERACTIONS */}
            {tab === 'interactions' && (
              <div className="space-y-4 animate-fade-in">
                {medicine.interactions.length > 0 ? (
                  <InteractionsPanel interactions={medicine.interactions} />
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                    <ShieldAlert className="w-10 h-10 text-emerald-400/40" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">No major drug interactions recorded.</p>
                  </div>
                )}
                {medicine.ageWarnings.length > 0 && (
                  <AgeWarningsPanel warnings={medicine.ageWarnings} patientAge={patientAge} />
                )}
              </div>
            )}

            {/* LIFESTYLE */}
            {tab === 'lifestyle' && (
              <div className="space-y-2 animate-fade-in">
                {medicine.lifestyleRecommendations.length > 0 ? (
                  medicine.lifestyleRecommendations.map((rec, i) => {
                    const lc = LIFESTYLE_COLORS[rec.severity] ?? LIFESTYLE_COLORS.moderate
                    return (
                      <div
                        key={rec.id}
                        className={cn('rounded-xl border p-3.5 space-y-1.5 animate-fade-up opacity-0', lc.bg, lc.border)}
                        style={{ animationDelay: `${i * 0.07}s`, animationFillMode: 'forwards' }}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-base">{LIFESTYLE_EMOJI[rec.category] ?? '💊'}</span>
                          <p className={cn('text-sm font-semibold', lc.text)}>{rec.title}</p>
                          <span className={cn('ml-auto label-mono px-1.5 py-0.5 rounded-full border', lc.bg, lc.border, lc.text)} style={{ fontSize: '0.56rem' }}>
                            {rec.severity.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{rec.description}</p>
                      </div>
                    )
                  })
                ) : (
                  <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                    <Leaf className="w-10 h-10 text-[#0DCDAA]/30" />
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">No specific lifestyle restrictions noted.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
