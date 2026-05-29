import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'

export const metadata: Metadata = {
  title: 'RxExplain — AI Prescription Safety Assistant',
  description:
    'Upload your prescription and get instant AI-powered analysis: medicine explanations, side effects, drug interactions, dosage warnings, and lifestyle recommendations.',
  keywords: ['prescription', 'medicine', 'drug interactions', 'side effects', 'healthcare AI', 'medication safety'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="rx-bg-mesh antialiased">
        {/* Grid overlay */}
        <div
          aria-hidden="true"
          className="fixed inset-0 pointer-events-none opacity-50 bg-grid"
        />
        <div className="relative min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1 pt-16">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  )
}
