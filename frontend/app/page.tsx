import Link from 'next/link'
import {
  UploadCloud, Zap, ShieldCheck, AlertTriangle,
  Brain, Activity, ArrowRight, Pill, FileSearch, CheckCircle,
} from 'lucide-react'

const FEATURES = [
  {
    icon: FileSearch,
    title: 'OCR Text Extraction',
    description: 'Reads handwritten and printed prescriptions via advanced optical character recognition.',
    accent: '#0DCDAA',
  },
  {
    icon: Brain,
    title: 'AI Drug Analysis',
    description: 'Plain-language explanations of every medicine, sourced from comprehensive drug databases.',
    accent: '#3A7FD4',
  },
  {
    icon: ShieldCheck,
    title: 'Interaction Checker',
    description: 'Flags dangerous drug-drug and drug-food combinations with severity ratings.',
    accent: '#8B5CF6',
  },
  {
    icon: AlertTriangle,
    title: 'Dosage Warnings',
    description: 'Highlights overdose thresholds, missed dose protocols, and age-adjusted dosing.',
    accent: '#F59E0B',
  },
  {
    icon: Activity,
    title: 'Side Effect Profiles',
    description: 'Comprehensive side effect lists with frequency data and watch-out severity levels.',
    accent: '#F97316',
  },
  {
    icon: Zap,
    title: 'Drowsiness Alerts',
    description: 'Clear driving and machinery safety alerts based on each medication\'s sedation profile.',
    accent: '#EF4444',
  },
]

const STEPS = [
  { n: '01', title: 'Upload Prescription', desc: 'Take a photo or scan of your prescription and upload it — JPG, PNG, or PDF.' },
  { n: '02', title: 'AI Analyses',         desc: 'Our AI extracts text and cross-references drug databases in under 3 seconds.' },
  { n: '03', title: 'Review Report',        desc: 'Get a full safety report with interactions, warnings, dosage info, and lifestyle advice.' },
]

export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="pt-20 pb-16 md:pt-28 md:pb-24 text-center relative">
        {/* Ambient blobs */}
        <div aria-hidden="true" className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none w-[640px] h-[420px]">
          <div className="absolute inset-0 bg-[#0DCDAA]/7 rounded-full blur-3xl" />
          <div className="absolute inset-12 bg-[#3A7FD4]/5 rounded-full blur-3xl" />
        </div>

        <div className="relative space-y-6">
          {/* Status badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0DCDAA]/10 border border-[#0DCDAA]/25 animate-fade-in">
            <span className="w-1.5 h-1.5 rounded-full bg-[#0DCDAA] animate-pulse" />
            <span className="label-mono text-[#0DCDAA]" style={{ fontSize: '0.62rem' }}>
              AI-POWERED · PRIVACY-FIRST · FREE TO USE
            </span>
          </div>

          <h1
            className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.1] animate-fade-up opacity-0 stagger-1"
            style={{ animationFillMode: 'forwards', color: 'hsl(var(--foreground))' }}
          >
            Understand Your
            <br />
            <span style={{ background: 'linear-gradient(135deg, #0DCDAA 0%, #3A7FD4 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Prescription Safely
            </span>
          </h1>

          <p
            className="text-base sm:text-lg max-w-2xl mx-auto leading-relaxed animate-fade-up opacity-0 stagger-2"
            style={{ animationFillMode: 'forwards', color: 'hsl(var(--muted-foreground))' }}
          >
            Upload any prescription and receive instant AI-powered explanations of every medicine — including side effects, drug interactions, dosage warnings, and personalised lifestyle recommendations.
          </p>

          <div
            className="flex flex-col sm:flex-row gap-3 justify-center pt-2 animate-fade-up opacity-0 stagger-3"
            style={{ animationFillMode: 'forwards' }}
          >
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm transition-all active:scale-95"
              style={{ background: '#0DCDAA', color: '#071A14', boxShadow: '0 0 24px rgba(13,205,170,0.2)' }}
            >
              <UploadCloud className="w-4 h-4" />
              Upload Prescription
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/results"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm transition-all border"
              style={{ background: 'hsl(var(--secondary))', borderColor: 'hsl(var(--border))', color: 'hsl(var(--foreground))' }}
            >
              <Activity className="w-4 h-4" style={{ color: 'hsl(var(--muted-foreground))' }} />
              View Demo Report
            </Link>
          </div>

          {/* Trust row */}
          <div
            className="flex flex-wrap items-center justify-center gap-4 pt-4 animate-fade-up opacity-0 stagger-4"
            style={{ animationFillMode: 'forwards' }}
          >
            {['No login required', 'Data stays local', 'Instant results', '10 000+ drug database'].map((t) => (
              <div key={t} className="flex items-center gap-1.5">
                <CheckCircle className="w-3 h-3 text-[#0DCDAA]" />
                <span className="label-mono" style={{ fontSize: '0.62rem', color: 'hsl(var(--muted-foreground))' }}>{t}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────────── */}
      <section className="py-12 border-t" style={{ borderColor: 'hsl(var(--border)/0.4)' }}>
        <div className="text-center mb-10">
          <p className="label-mono text-[#0DCDAA] mb-2" style={{ fontSize: '0.62rem' }}>HOW IT WORKS</p>
          <h2 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
            Three steps to safety
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x rounded-2xl overflow-hidden border" style={{ borderColor: 'hsl(var(--border)/0.5)' }}>
          {STEPS.map(({ n, title, desc }) => (
            <div key={n} className="p-6 space-y-3 group transition-colors" style={{ background: 'hsl(var(--card))' }}>
              <span className="font-mono text-4xl font-extrabold" style={{ color: 'rgba(13,205,170,0.18)' }}>{n}</span>
              <h3 className="text-base font-bold" style={{ color: 'hsl(var(--foreground))' }}>{title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: 'hsl(var(--muted-foreground))' }}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────────── */}
      <section className="py-16">
        <div className="text-center mb-10">
          <p className="label-mono text-[#0DCDAA] mb-2" style={{ fontSize: '0.62rem' }}>CAPABILITIES</p>
          <h2 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
            Everything you need to know
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, description, accent }, i) => (
            <div
              key={title}
              className={`rounded-2xl border p-5 space-y-3 rx-hover-glow animate-fade-up opacity-0 stagger-${Math.min(i + 1, 6)}`}
              style={{
                background: 'hsl(var(--card))',
                borderColor: 'hsl(var(--border)/0.6)',
                animationFillMode: 'forwards',
              }}
            >
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center border"
                style={{ background: `${accent}18`, borderColor: `${accent}30` }}
              >
                <Icon className="w-5 h-5" style={{ color: accent }} />
              </div>
              <h3 className="text-sm font-bold" style={{ color: 'hsl(var(--foreground))' }}>{title}</h3>
              <p className="text-xs leading-relaxed" style={{ color: 'hsl(var(--muted-foreground))' }}>{description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────────── */}
      <section className="py-12 mb-8">
        <div
          className="relative rounded-2xl border p-8 sm:p-12 text-center overflow-hidden"
          style={{
            background: 'linear-gradient(135deg, rgba(13,205,170,0.07) 0%, rgba(58,127,212,0.04) 100%)',
            borderColor: 'rgba(13,205,170,0.2)',
          }}
        >
          <div aria-hidden="true" className="absolute inset-0 bg-grid opacity-60 pointer-events-none" />
          <div className="relative space-y-5">
            <Pill className="w-10 h-10 text-[#0DCDAA] mx-auto" />
            <h2 className="text-2xl sm:text-3xl font-bold" style={{ color: 'hsl(var(--foreground))' }}>
              Ready to decode your prescription?
            </h2>
            <p className="text-sm max-w-md mx-auto" style={{ color: 'hsl(var(--muted-foreground))' }}>
              Upload in seconds. Get a full safety report powered by AI and validated medical databases.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-sm transition-all active:scale-95"
              style={{ background: '#0DCDAA', color: '#071A14', boxShadow: '0 0 28px rgba(13,205,170,0.25)' }}
            >
              <UploadCloud className="w-4 h-4" />
              Upload Prescription Free
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
