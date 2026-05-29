import { Pill, Shield, AlertTriangle } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="mt-24 border-t border-[hsl(var(--border)/0.5)] bg-[hsl(var(--card)/0.4)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Pill className="w-4 h-4 text-[#0DCDAA]" />
              <span className="font-bold text-sm text-[hsl(var(--foreground))]">RxExplain</span>
            </div>
            <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed max-w-xs">
              AI-powered prescription analysis for better patient understanding and medication safety awareness.
            </p>
          </div>

          <div>
            <p className="label-mono text-[hsl(var(--muted-foreground))] mb-3" style={{ fontSize: '0.58rem' }}>
              FEATURES
            </p>
            <ul className="space-y-2 text-xs text-[hsl(var(--muted-foreground))]">
              {[
                'Prescription OCR',
                'Drug Interaction Check',
                'Side Effect Analysis',
                'Dosage Verification',
                'Drowsiness Alerts',
                'Lifestyle Recommendations',
              ].map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/15">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <p className="label-mono text-amber-400" style={{ fontSize: '0.58rem' }}>
                MEDICAL DISCLAIMER
              </p>
            </div>
            <p className="text-xs text-[hsl(var(--muted-foreground))] leading-relaxed">
              This tool is for informational purposes only and does not constitute medical advice. Always consult a qualified healthcare professional before making any medication decisions.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between pt-6 border-t border-[hsl(var(--border)/0.4)] gap-3">
          <div className="flex items-center gap-2">
            <Shield className="w-3 h-3 text-[#0DCDAA]" />
            <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
              PROCESSED IN-MEMORY · NEVER STORED
            </span>
          </div>
          <span className="label-mono text-[hsl(var(--muted-foreground))]" style={{ fontSize: '0.58rem' }}>
            © {new Date().getFullYear()} RXEXPLAIN · NOT A SUBSTITUTE FOR MEDICAL ADVICE
          </span>
        </div>
      </div>
    </footer>
  )
}
