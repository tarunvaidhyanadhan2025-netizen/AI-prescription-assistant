'use client'

import { cn } from '@/lib/utils'
import { Loader2, FileSearch, Database, Zap, CheckCircle, Cpu } from 'lucide-react'

interface LoadingStateProps {
  step?: string
  progress?: number
  variant?: 'upload' | 'processing' | 'inline'
  className?: string
}

export default function LoadingState({
  step = 'Processing…',
  progress = 0,
  variant = 'processing',
  className,
}: LoadingStateProps) {
  if (variant === 'inline') {
    return (
      <div className={cn('flex items-center gap-2', className)}>
        <Loader2 className="w-4 h-4 text-[#0DCDAA] animate-spin" />
        <span className="label-mono text-[hsl(var(--muted-foreground))] text-xs">{step}</span>
      </div>
    )
  }

  if (variant === 'upload') {
    return (
      <div className={cn('flex flex-col items-center gap-6 py-8', className)}>
        <div className="relative w-20 h-20">
          <div className="absolute inset-0 rounded-2xl bg-[#0DCDAA]/10 border border-[#0DCDAA]/20 animate-pulse" />
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-[#0DCDAA] animate-spin" />
          </div>
          {/* Bracket corners */}
          {[
            'top-0 left-0 border-t-2 border-l-2 rounded-tl-lg',
            'top-0 right-0 border-t-2 border-r-2 rounded-tr-lg',
            'bottom-0 left-0 border-b-2 border-l-2 rounded-bl-lg',
            'bottom-0 right-0 border-b-2 border-r-2 rounded-br-lg',
          ].map((cls, i) => (
            <div key={i} className={cn('absolute w-4 h-4 border-[#0DCDAA]', cls)} />
          ))}
        </div>
        <div className="text-center space-y-1">
          <p className="text-sm font-medium text-[hsl(var(--foreground))]">Uploading Prescription</p>
          <p className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.6rem' }}>{progress}% COMPLETE</p>
        </div>
        <div className="w-56 h-1 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#0DCDAA] to-[#3A7FD4] rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    )
  }

  // Processing variant
  const STEP_ICONS = [FileSearch, Database, Cpu, Zap, CheckCircle]

  return (
    <div className={cn('flex flex-col items-center gap-8 py-10', className)}>
      {/* Animated orb */}
      <div className="relative w-24 h-24 flex items-center justify-center">
        <div className="absolute inset-0 rounded-full border border-[#0DCDAA]/15 animate-spin" style={{ animationDuration: '9s' }} />
        <div className="absolute inset-2 rounded-full border border-[#3A7FD4]/15 animate-spin" style={{ animationDuration: '5s', animationDirection: 'reverse' }} />
        <div className="absolute inset-4 rounded-full bg-[#0DCDAA]/8 border border-[#0DCDAA]/25 flex items-center justify-center">
          <Zap className="w-6 h-6 text-[#0DCDAA]" />
        </div>
        {/* Orbiting dot */}
        <div
          className="absolute w-2.5 h-2.5 rounded-full bg-[#0DCDAA] shadow-rx-glow"
          style={{
            top: '4px',
            left: '50%',
            marginLeft: '-5px',
            transformOrigin: '5px 44px',
            animation: 'spin 3s linear infinite',
          }}
        />
      </div>

      <div className="text-center space-y-2">
        <h3 className="text-base font-semibold text-[hsl(var(--foreground))]">Analysing Prescription</h3>
        <p className="label-mono text-[#0DCDAA] tracking-widest" style={{ fontSize: '0.62rem' }}>{step}</p>
      </div>

      {/* Step icon pills */}
      <div className="flex items-center gap-2">
        {STEP_ICONS.map((Icon, i) => (
          <div
            key={i}
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-[hsl(var(--border))] bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]"
          >
            <Icon className="w-3.5 h-3.5" />
          </div>
        ))}
      </div>

      {/* Horizontal scan bar */}
      <div className="w-56 relative h-px bg-[hsl(var(--border)/0.5)] rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 w-12 bg-gradient-to-r from-transparent via-[#0DCDAA] to-transparent"
          style={{ animation: 'scanH 1.8s ease-in-out infinite' }}
        />
      </div>

      <style>{`
        @keyframes scanH {
          0%   { left: -48px; }
          100% { left: 100%; }
        }
      `}</style>

      <p className="text-xs text-[hsl(var(--muted-foreground))] max-w-xs text-center leading-relaxed">
        Cross-referencing drug interactions, safety profiles, and dosage guidelines with medical databases.
      </p>
    </div>
  )
}

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-xl border border-[hsl(var(--border)/0.5)] p-5 space-y-3', className)}>
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg skeleton-shimmer" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-36 rounded skeleton-shimmer" />
          <div className="h-3 w-24 rounded skeleton-shimmer" />
        </div>
        <div className="h-5 w-16 rounded-full skeleton-shimmer" />
      </div>
      <div className="space-y-2 pt-1">
        <div className="h-3 w-full rounded skeleton-shimmer" />
        <div className="h-3 w-4/5 rounded skeleton-shimmer" />
        <div className="h-3 w-3/5 rounded skeleton-shimmer" />
      </div>
    </div>
  )
}
