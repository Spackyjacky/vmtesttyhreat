import Link from 'next/link'
import type { Metadata } from 'next'
import Navbar from '@/components/marketing/navbar'
import Footer from '@/components/marketing/footer'
import BackgroundFX from '@/components/marketing/background-fx'
import { ArrowRightIcon } from '@/components/marketing/icons'
import { SUMUP_BOOKING_URL } from '@/lib/site'

export const metadata: Metadata = {
  title: 'Page Not Found',
  robots: { index: false, follow: true },
}

export default function NotFound() {
  return (
    <div className="site-scope flex min-h-screen flex-col bg-brand-bg text-brand-white">
      <BackgroundFX />
      <Navbar />
      <main className="flex-1">
        <section className="section flex flex-col items-center py-24 text-center sm:py-32">
          <span className="eyebrow mb-4">Error 404</span>
          <h1 className="font-display text-[clamp(2.4rem,6vw,4rem)] font-bold tracking-[-0.01em] text-brand-white">
            404, <span className="text-brand-blue-bright">Fixed.</span>
          </h1>
          <p className="mt-5 max-w-md text-lg text-brand-muted">
            This page doesn&apos;t exist — but we can still fix your WiFi. Let&apos;s get you back
            on the network.
          </p>
          <div className="mt-9 flex flex-wrap justify-center gap-3.5">
            <Link href="/" className="btn-brand">
              Back home <ArrowRightIcon size={16} />
            </Link>
            <a className="btn-brand-outline" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book a visit
            </a>
          </div>

          <div className="mt-16 w-full max-w-md rounded-[10px] border border-brand-border bg-brand-bg-alt p-4 font-mono text-sm text-brand-muted">
            <p className="mb-1.5">
              <span className="mr-1.5 text-brand-blue-bright">&gt;</span>resolving requested page...
            </p>
            <p>
              <span className="mr-1.5 text-brand-blue-bright">&gt;</span>404 — PAGE NOT FOUND
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
