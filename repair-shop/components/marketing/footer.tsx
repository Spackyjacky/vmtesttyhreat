import Link from 'next/link'
import Logo from './logo'
import { services } from '@/lib/services'
import { CONTACT_EMAIL, SERVICE_AREA, SUMUP_BOOKING_URL } from '@/lib/site'

export default function Footer() {
  return (
    <footer className="border-t border-brand-border">
      <div className="section mx-auto max-w-7xl py-11">
        <div className="mb-7 flex flex-wrap items-start justify-between gap-8">
          <div>
            <Logo />
            <p className="mt-2.5 max-w-[32ch] text-sm text-brand-muted">
              Reliable IT support, network installs and WiFi help across {SERVICE_AREA}. Fixed right.
            </p>
          </div>

          <div className="flex flex-wrap gap-12">
            <div>
              <h4 className="mb-3.5 text-[13px] uppercase tracking-wide text-brand-muted-2">Services</h4>
              {services.map((s) => (
                <Link key={s.slug} href={`/services/${s.slug}`} className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                  {s.name}
                </Link>
              ))}
            </div>
            <div>
              <h4 className="mb-3.5 text-[13px] uppercase tracking-wide text-brand-muted-2">Site</h4>
              <Link href="/about" className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                How it works
              </Link>
              <Link href="/services" className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                Coverage
              </Link>
              <Link href="/contact" className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                Contact
              </Link>
              <Link href="/login" className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                Staff login
              </Link>
            </div>
            <div>
              <h4 className="mb-3.5 text-[13px] uppercase tracking-wide text-brand-muted-2">Contact</h4>
              <a href={`mailto:${CONTACT_EMAIL}`} className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                {CONTACT_EMAIL}
              </a>
              <a href={SUMUP_BOOKING_URL} target="_blank" rel="noopener" className="mb-2.5 block text-sm text-brand-muted hover:text-brand-white">
                Book a visit
              </a>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-brand-border pt-6 text-sm text-brand-muted-2">
          <span>&copy; {new Date().getFullYear()} 404 Fixed. {SERVICE_AREA}.</span>
          <span>Reliable IT solutions. Fixed right.</span>
        </div>
      </div>
    </footer>
  )
}
