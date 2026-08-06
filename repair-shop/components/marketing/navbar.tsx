'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import Logo from './logo'
import { services } from '@/lib/services'
import { SUMUP_BOOKING_URL } from '@/lib/site'
import { MenuIcon, CloseIcon, ChevronDownIcon } from './icons'

const NAV_LINKS = [
  { label: 'Services', href: '/services' },
  { label: 'How it works', href: '/about' },
  { label: 'Contact', href: '/contact' },
]

export default function Navbar() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const [servicesOpen, setServicesOpen] = useState(false)

  useEffect(() => {
    setOpen(false)
  }, [pathname])

  return (
    <header className="sticky top-0 z-50 border-b border-brand-border bg-brand-bg/75 backdrop-blur-md">
      <div className="section mx-auto flex max-w-7xl items-center justify-between py-4">
        <Logo />

        <nav className="hidden items-center gap-1 lg:flex">
          {NAV_LINKS.map((link) => {
            if (link.label === 'Services') {
              return (
                <div
                  key={link.href}
                  className="relative"
                  onMouseEnter={() => setServicesOpen(true)}
                  onMouseLeave={() => setServicesOpen(false)}
                >
                  <Link
                    href={link.href}
                    className={`flex items-center gap-1 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      pathname.startsWith('/services') ? 'text-brand-white' : 'text-brand-muted hover:text-brand-white'
                    }`}
                  >
                    Services <ChevronDownIcon />
                  </Link>
                  {servicesOpen && (
                    <div className="absolute left-1/2 top-full w-72 -translate-x-1/2 pt-2">
                      <div className="rounded-2xl border border-brand-border-strong bg-brand-surface p-2 shadow-2xl shadow-black/40">
                        {services.map((s) => (
                          <Link
                            key={s.slug}
                            href={`/services/${s.slug}`}
                            className="block rounded-xl px-4 py-2.5 text-sm text-brand-white hover:bg-brand-surface-2"
                          >
                            <span className="font-medium">{s.name}</span>
                            <span className="block text-xs text-brand-muted">{s.tagline}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            }
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                  pathname === link.href ? 'text-brand-white' : 'text-brand-muted hover:text-brand-white'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>

        <div className="hidden lg:block">
          <a className="btn-brand" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
            Book now
          </a>
        </div>

        <button
          type="button"
          aria-label="Toggle menu"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-brand-border-strong text-brand-white lg:hidden"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>

      {open && (
        <div className="border-t border-brand-border bg-brand-bg lg:hidden">
          <nav className="section mx-auto flex max-w-7xl flex-col gap-1 py-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-xl px-3 py-2.5 text-sm font-medium text-brand-white hover:bg-brand-surface"
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-2 border-t border-brand-border pt-3">
              {services.map((s) => (
                <Link
                  key={s.slug}
                  href={`/services/${s.slug}`}
                  className="block rounded-xl px-3 py-2 text-sm text-brand-muted hover:bg-brand-surface hover:text-brand-white"
                >
                  {s.name}
                </Link>
              ))}
            </div>
            <a className="btn-brand mt-3 justify-center" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book now
            </a>
          </nav>
        </div>
      )}
    </header>
  )
}
