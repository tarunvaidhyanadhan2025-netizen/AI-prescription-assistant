import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { SeverityLevel, DrowsinessLevel } from '@/types/medicine'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function getSeverityColor(severity: SeverityLevel) {
  const map = {
    low: {
      bg: 'bg-emerald-500/10',
      text: 'text-emerald-400',
      border: 'border-emerald-500/20',
      badge: 'bg-emerald-500/15 text-emerald-400',
    },
    moderate: {
      bg: 'bg-amber-500/10',
      text: 'text-amber-400',
      border: 'border-amber-500/20',
      badge: 'bg-amber-500/15 text-amber-400',
    },
    high: {
      bg: 'bg-orange-500/10',
      text: 'text-orange-400',
      border: 'border-orange-500/20',
      badge: 'bg-orange-500/15 text-orange-400',
    },
    critical: {
      bg: 'bg-red-500/10',
      text: 'text-red-400',
      border: 'border-red-500/20',
      badge: 'bg-red-500/15 text-red-400',
    },
  }
  return map[severity]
}

export function getDrowsinessConfig(level: DrowsinessLevel) {
  const map = {
    none: {
      label: 'No Drowsiness',
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      description: 'This medication does not typically cause drowsiness.',
    },
    mild: {
      label: 'Mild Drowsiness',
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
      description: 'May cause mild drowsiness. Exercise caution when driving.',
    },
    moderate: {
      label: 'Moderate Drowsiness',
      color: 'text-orange-400',
      bgColor: 'bg-orange-500/10',
      description: 'Likely to cause drowsiness. Avoid driving or operating heavy machinery.',
    },
    severe: {
      label: 'Severe Drowsiness',
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      description: 'Will cause significant drowsiness. Do NOT drive or operate machinery.',
    },
  }
  return map[level]
}

export function getFrequencyLabel(freq: string): string {
  const map: Record<string, string> = {
    common: 'Common (>10%)',
    uncommon: 'Uncommon (1–10%)',
    rare: 'Rare (<1%)',
  }
  return map[freq] || freq
}

export function formatTimestamp(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return 'High'
  if (confidence >= 0.7) return 'Moderate'
  return 'Low'
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'text-emerald-400'
  if (confidence >= 0.7) return 'text-amber-400'
  return 'text-red-400'
}

export const ACCEPTED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'application/pdf',
  'image/heic',
]

export const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB
