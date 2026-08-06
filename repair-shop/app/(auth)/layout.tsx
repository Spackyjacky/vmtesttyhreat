import type { Metadata } from 'next'

export const metadata: Metadata = {
  manifest: '/manifest.json',
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <main className="dashboard-scope min-h-screen bg-bg text-fg flex items-center justify-center p-4">
      {children}
    </main>
  )
}
