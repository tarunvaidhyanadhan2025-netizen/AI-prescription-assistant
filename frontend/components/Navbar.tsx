'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Activity, Moon, Sun, Menu, X, Pill } from 'lucide-react'

const NAV_LINKS = [
  { href: '/',        label: 'Home'     },
  { href: '/upload',  label: 'Upload Rx' },
  { href: '/results', label: 'Results'  },
  { href: '/history', label: 'History'  },
]

export default function Navbar() {
  const pathname = usePathname()
  const [scrolled, setScrolled] = useState(false)
  const [dark, setDark]         = useState(true)
  const [open, setOpen]         = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('light', !dark)
  }, [dark])

  useEffect(() => {
    const h = () => setScrolled(window.scrollY > 8)
    window.addEventListener('scroll', h, { passive: true })
    return () => window.removeEventListener('scroll', h)
  }, [])

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        scrolled
          ? 'bg-[hsl(var(--background)/0.85)] backdrop-blur-xl border-b border-[hsl(var(--border)/0.6)] shadow-[0_4px_24px_rgba(0,0,0,0.3)]'
          : 'bg-transparent'
      )}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group shrink-0">
          <div className="relative w-8 h-8 flex items-center justify-center rounded-lg bg-[#0DCDAA]/15 border border-[#0DCDAA]/30 group-hover:bg-[#0DCDAA]/25 transition-colors">
            <Pill className="w-4 h-4 text-[#0DCDAA]" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#0DCDAA] animate-pulse" />
          </div>
          <div className="leading-none">
            <div className="text-sm font-bold tracking-tight text-[hsl(var(--foreground))]">RxLens</div>
            <div className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.55rem' }}>
              AI SAFETY ASSISTANT
            </div>
          </div>
        </Link>

        {/* Desktop links */}
        <ul className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ href, label }) => (
            <li key={href}>
              <Link
                href={href}
                className={cn(
                  'px-4 py-2 rounded-lg label-mono text-xs transition-colors',
                  pathname === href
                    ? 'bg-[#0DCDAA]/10 text-[#0DCDAA] border border-[#0DCDAA]/20'
                    : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))]'
                )}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <Activity className="w-3 h-3 text-emerald-400" />
            <span className="label-mono text-emerald-400" style={{ fontSize: '0.58rem' }}>SYSTEM ONLINE</span>
          </div>

          <button
            onClick={() => setDark((d) => !d)}
            className="p-2 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors"
            aria-label="Toggle dark mode"
          >
            {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <button
            onClick={() => setOpen((o) => !o)}
            className="md:hidden p-2 rounded-lg text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))] transition-colors"
            aria-label="Toggle menu"
          >
            {open ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      {open && (
        <div className="md:hidden border-t border-[hsl(var(--border)/0.6)] bg-[hsl(var(--background)/0.95)] backdrop-blur-xl px-4 py-3 space-y-1">
          {NAV_LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={cn(
                'block px-4 py-2.5 rounded-lg label-mono text-xs transition-colors',
                pathname === href
                  ? 'bg-[#0DCDAA]/10 text-[#0DCDAA]'
                  : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))]'
              )}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  )
}
