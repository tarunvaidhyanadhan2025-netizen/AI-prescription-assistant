'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { cn, formatFileSize, ACCEPTED_MIME_TYPES, MAX_FILE_SIZE } from '@/lib/utils'
import { UploadCloud, FileImage, X, AlertCircle, CheckCircle2 } from 'lucide-react'

interface UploadDropzoneProps {
  onFileAccepted: (file: File) => void
  onError?: (msg: string) => void
  disabled?: boolean
  className?: string
}

export default function UploadDropzone({ onFileAccepted, onError, disabled, className }: UploadDropzoneProps) {
  const [preview, setPreview] = useState<{ url: string; name: string; size: number } | null>(null)
  const [dragError, setDragError] = useState<string | null>(null)

  const onDrop = useCallback(
    (accepted: File[], rejected: import('react-dropzone').FileRejection[]) => {
      setDragError(null)
      if (rejected.length > 0) {
        const msg = rejected[0]?.errors?.[0]?.message || 'File rejected.'
        setDragError(msg)
        onError?.(msg)
        return
      }
      if (accepted[0]) {
        const file = accepted[0]
        setPreview({ url: URL.createObjectURL(file), name: file.name, size: file.size })
        onFileAccepted(file)
      }
    },
    [onFileAccepted, onError]
  )

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: Object.fromEntries(ACCEPTED_MIME_TYPES.map((t) => [t, []])),
    maxSize: MAX_FILE_SIZE,
    maxFiles: 1,
    disabled,
  })

  const clearPreview = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (preview) URL.revokeObjectURL(preview.url)
    setPreview(null)
    setDragError(null)
  }

  const isImage = preview && !preview.name.toLowerCase().endsWith('.pdf')

  return (
    <div className={cn('w-full', className)}>
      <div
        {...getRootProps()}
        className={cn(
          'relative group cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300 outline-none',
          'min-h-[220px] flex flex-col items-center justify-center overflow-hidden',
          isDragActive && !isDragReject && 'border-[#0DCDAA] bg-[#0DCDAA]/5 scale-[1.015]',
          isDragReject && 'border-red-500 bg-red-500/5',
          dragError && !isDragActive && 'border-red-500/50',
          !isDragActive && !dragError && !preview && 'border-[hsl(var(--border)/0.6)] hover:border-[#0DCDAA]/50 hover:bg-[#0DCDAA]/3',
          preview && !dragError && 'border-[#0DCDAA]/30 bg-[#0DCDAA]/3',
          disabled && 'opacity-50 cursor-not-allowed pointer-events-none'
        )}
      >
        <input {...getInputProps()} aria-label="Upload prescription file" />

        {/* Scan line when dragging */}
        {isDragActive && (
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            <div
              className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#0DCDAA] to-transparent"
              style={{ animation: 'scanH 1.4s linear infinite' }}
            />
          </div>
        )}

        {/* Corner brackets */}
        {['top-3 left-3 border-t-2 border-l-2 rounded-tl', 'top-3 right-3 border-t-2 border-r-2 rounded-tr',
          'bottom-3 left-3 border-b-2 border-l-2 rounded-bl', 'bottom-3 right-3 border-b-2 border-r-2 rounded-br'].map((cls, i) => (
          <div
            key={i}
            className={cn(
              'absolute w-5 h-5 transition-colors duration-300',
              cls,
              isDragActive && !isDragReject ? 'border-[#0DCDAA]' : 'border-[hsl(var(--border)/0.5)] group-hover:border-[#0DCDAA]/40'
            )}
          />
        ))}

        {preview ? (
          <div className="flex flex-col items-center gap-4 p-6 w-full">
            <div className="relative">
              {isImage ? (
                <div className="w-28 h-28 rounded-xl overflow-hidden border border-[#0DCDAA]/20 shadow-rx-card">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={preview.url} alt="Prescription preview" className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="w-28 h-28 rounded-xl bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] flex items-center justify-center">
                  <FileImage className="w-10 h-10 text-[hsl(var(--muted-foreground))]" />
                </div>
              )}
              <button
                onClick={clearPreview}
                className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors"
                aria-label="Remove file"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
            <div className="text-center space-y-1">
              <div className="flex items-center gap-2 justify-center">
                <CheckCircle2 className="w-4 h-4 text-[#0DCDAA]" />
                <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate max-w-[200px]">{preview.name}</p>
              </div>
              <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.6rem' }}>
                {formatFileSize(preview.size)} · READY TO ANALYSE
              </p>
            </div>
          </div>
        ) : dragError ? (
          <div className="flex flex-col items-center gap-3 p-6 text-center">
            <div className="w-14 h-14 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-red-400">File Rejected</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{dragError}</p>
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">Click to try again</p>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 p-8 text-center">
            <div className={cn(
              'w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300',
              isDragActive
                ? 'bg-[#0DCDAA]/20 border border-[#0DCDAA]/40 scale-110'
                : 'bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] group-hover:bg-[#0DCDAA]/10 group-hover:border-[#0DCDAA]/30'
            )}>
              <UploadCloud className={cn(
                'w-7 h-7 transition-colors duration-300',
                isDragActive ? 'text-[#0DCDAA]' : 'text-[hsl(var(--muted-foreground))] group-hover:text-[#0DCDAA]'
              )} />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-semibold text-[hsl(var(--foreground))]">
                {isDragActive ? 'Release to upload' : 'Drop prescription here'}
              </p>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">
                or <span className="text-[#0DCDAA] underline underline-offset-2">click to browse</span>
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {['JPG', 'PNG', 'PDF', 'WEBP', 'HEIC'].map((ext) => (
                <span key={ext} className="label-mono px-2 py-0.5 rounded-md bg-[hsl(var(--secondary))] border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.6rem' }}>
                  {ext}
                </span>
              ))}
            </div>
            <p className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>MAX 10 MB</p>
          </div>
        )}
      </div>
    </div>
  )
}
