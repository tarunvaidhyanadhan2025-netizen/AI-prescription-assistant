'use client'

import { cn } from '@/lib/utils'
import type { DosageInfo } from '@/types/medicine'
import { Clock, Utensils, Droplets, AlertTriangle, Info, RefreshCw } from 'lucide-react'

interface DosageSafetyCardProps {
  dosage: DosageInfo
  medicineName: string
  className?: string
}

export default function DosageSafetyCard({ dosage, medicineName: _, className }: DosageSafetyCardProps) {
  const grid = [
    { icon: Clock,         label: 'Standard Dose', value: dosage.standard, color: 'text-[#0DCDAA]',   bg: 'bg-[#0DCDAA]/10',    border: 'border-[#0DCDAA]/20' },
    { icon: AlertTriangle, label: 'Max Dose',       value: dosage.maximum,  color: 'text-amber-400',   bg: 'bg-amber-500/10',    border: 'border-amber-500/20' },
    { icon: RefreshCw,     label: 'Frequency',      value: dosage.frequency,color: 'text-[#3A7FD4]',   bg: 'bg-[#3A7FD4]/10',   border: 'border-[#3A7FD4]/20' },
    { icon: Info,          label: 'Route',          value: dosage.route,    color: 'text-violet-400',  bg: 'bg-violet-500/10',   border: 'border-violet-500/20' },
  ]

  return (
    <div className={cn('rounded-xl border border-[hsl(var(--border)/0.6)] bg-[hsl(var(--card))] p-4 space-y-4', className)}>
      <div className="flex items-center gap-2">
        <Clock className="w-4 h-4 text-[#0DCDAA]" />
        <h4 className="text-sm font-semibold text-[hsl(var(--foreground))]">Dosage & Administration</h4>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {grid.map(({ icon: Icon, label, value, color, bg, border }) => (
          <div key={label} className={cn('rounded-lg border p-3 space-y-1', bg, border)}>
            <div className="flex items-center gap-1.5">
              <Icon className={cn('w-3 h-3', color)} />
              <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.56rem' }}>
                {label.toUpperCase()}
              </p>
            </div>
            <p className={cn('text-sm font-semibold leading-snug', color)}>{value}</p>
          </div>
        ))}
      </div>

      {/* Take with */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>TAKE WITH:</span>
        {dosage.withFood && (
          <span className="flex items-center gap-1 label-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" style={{ fontSize: '0.58rem' }}>
            <Utensils style={{ width: 10, height: 10 }} /> FOOD
          </span>
        )}
        {dosage.withWater && (
          <span className="flex items-center gap-1 label-mono px-2 py-0.5 rounded-full bg-[#3A7FD4]/10 text-[#3A7FD4] border border-[#3A7FD4]/20" style={{ fontSize: '0.58rem' }}>
            <Droplets style={{ width: 10, height: 10 }} /> WATER
          </span>
        )}
        {!dosage.withFood && !dosage.withWater && (
          <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>No specific requirement</span>
        )}
      </div>

      {/* Missed dose */}
      {dosage.missedDose && (
        <div className="rounded-lg border border-[#3A7FD4]/20 bg-[#3A7FD4]/5 p-3 space-y-1">
          <p className="label-mono text-[#3A7FD4]" style={{ fontSize: '0.58rem' }}>IF DOSE IS MISSED</p>
          <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">{dosage.missedDose}</p>
        </div>
      )}

      {/* Overdose */}
      {dosage.overdoseWarning && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-3 space-y-1">
          <p className="label-mono text-red-400" style={{ fontSize: '0.58rem' }}>⚠ OVERDOSE WARNING</p>
          <p className="text-xs text-red-300 leading-relaxed">{dosage.overdoseWarning}</p>
        </div>
      )}
    </div>
  )
}
