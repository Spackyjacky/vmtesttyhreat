import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import Sidebar from '@/components/sidebar'

// The staff app is installable as a PWA — the public marketing site (root layout) isn't,
// so the manifest link lives here rather than site-wide.
export const metadata: Metadata = {
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: process.env.NEXT_PUBLIC_APP_NAME ?? '404 Fixed',
  },
}

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  return (
    <div className="dashboard-scope min-h-screen bg-bg text-fg">
      <Sidebar userEmail={user.email} />
      {/* Main content — offset for sidebar on desktop, top bar on mobile */}
      <main className="lg:pl-64 pt-14 lg:pt-0 min-h-screen">
        <div className="p-4 sm:p-6 max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}
