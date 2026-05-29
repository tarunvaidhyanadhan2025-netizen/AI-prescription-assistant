'use client'

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ZoomIn, ZoomOut, RotateCw, FileText, Copy, Check } from 'lucide-react'

interface PrescriptionPreviewProps {
  previewUrl: string | null
  ocrText: string | null
  fileName?: string
  className?: string
}

export default function PrescriptionPreview({
  previewUrl,
  ocrText,
  fileName,
  className,
}: PrescriptionPreviewProps) {
  const [zoom, setZoom] = useState(100)
  const [rotation, setRotation] = useState(0)
  const [tab, setTab] = useState<'image' | 'text'>('image')
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    if (!ocrText) return
    await navigator.clipboard.writeText(ocrText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn('rounded-2xl border border-[hsl(var(--border)/0.6)] bg-[hsl(var(--card))] overflow-hidden', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[hsl(var(--border)/0.6)] bg-[hsl(var(--secondary)/0.3)]">
        <div className="flex items-center gap-2 min-w-0">
          <FileText className="w-4 h-4 text-[#0DCDAA] shrink-0" />
          <span className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
            {fileName || 'prescription.jpg'}
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {ocrText && (
            <div className="flex rounded-lg bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] overflow-hidden mr-2">
              {(['image', 'text'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={cn(
                    'px-3 py-1 label-mono transition-colors',
                    tab === t ? 'bg-[#0DCDAA]/15 text-[#0DCDAA]' : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                  )}
                  style={{ fontSize: '0.6rem' }}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>
          )}

          {tab === 'image' && previewUrl && (
            <>
              <button onClick={() => setZoom((z) => Math.max(50, z - 25))} className="p-1.5 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors" aria-label="Zoom out">
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="label-mono text-[hsl(var(--muted-foreground))] w-9 text-center" style={{ fontSize: '0.6rem' }}>{zoom}%</span>
              <button onClick={() => setZoom((z) => Math.min(200, z + 25))} className="p-1.5 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors" aria-label="Zoom in">
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => setRotation((r) => (r + 90) % 360)} className="p-1.5 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors" aria-label="Rotate">
                <RotateCw className="w-3.5 h-3.5" />
              </button>
            </>
          )}

          {tab === 'text' && ocrText && (
            <button onClick={copy} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors">
              {copied ? <Check className="w-3.5 h-3.5 text-[#0DCDAA]" /> : <Copy className="w-3.5 h-3.5" />}
              <span className="label-mono" style={{ fontSize: '0.6rem' }}>{copied ? 'COPIED' : 'COPY'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Preview area */}
      <div className="relative overflow-auto" style={{ background: '#0D0F14', maxHeight: '380px' }}>
        {tab === 'image' && previewUrl ? (
          <div className="flex items-center justify-center p-6 min-h-[200px] scan-overlay">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewUrl}
              alt="Prescription"
              style={{
                transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                transition: 'transform 0.2s ease',
                maxWidth: '100%',
                borderRadius: '8px',
                display: 'block',
              }}
            />
          </div>
        ) : tab === 'text' && ocrText ? (
          <pre className="p-4 text-xs font-mono text-[#0DCDAA]/80 leading-relaxed whitespace-pre-wrap overflow-auto">
            {ocrText}
          </pre>
        ) : (
          <div className="flex items-center justify-center min-h-[200px]">
            <p className="label-mono text-[hsl(var(--muted-foreground))] text-xs">NO PREVIEW AVAILABLE</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-[hsl(var(--border)/0.5)] bg-[hsl(var(--secondary)/0.2)] flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-[#0DCDAA] animate-pulse" />
          <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>OCR READY</span>
        </div>
        {ocrText && (
          <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
            {ocrText.trim().split(/\s+/).length} WORDS EXTRACTED
          </span>
        )}
      </div>
    </div>
  )
}
