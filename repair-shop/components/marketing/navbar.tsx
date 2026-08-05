'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import Logo from './logo'
import { services } from '@/lib/services'
import { MenuIcon, CloseIcon, ChevronDownIcon } from './icons'

const NAV_LINKS = [
  { label: 'Home', href: '/' },
  { label: 'Services', href: '/services' },
  { label: 'About', href: '/about' },
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
    <header className="sticky top-0 z-50 border-b border-brand-line bg-white/90 backdrop-blur">
      <div className="section mx-auto flex max-w-7xl items-center justify-between py-4">
        <Logo tagline />

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
                      pathname.startsWith('/services') ? 'text-brand-teal' : 'text-brand-ink hover:text-brand-teal'
                    }`}
                  >
                    Services <ChevronDownIcon />
                  </Link>
                  {servicesOpen && (
                    <div className="absolute left-1/2 top-full w-72 -translate-x-1/2 pt-2">
                      <div className="rounded-2xl border border-brand-line bg-white p-2 shadow-xl shadow-slate-900/5">
                        {services.map((s) => (
                          <Link
                            key={s.slug}
                            href={`/services/${s.slug}`}
                            className="block rounded-xl px-4 py-2.5 text-sm text-brand-ink hover:bg-brand-mist"
                          >
                            <span className="font-medium">{s.name}</span>
                            <span className="block text-xs text-brand-slate">{s.tagline}</span>
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
                  pathname === link.href ? 'text-brand-teal' : 'text-brand-ink hover:text-brand-teal'
                }`}
              >
                {link.label}
              </Link>
            )
          })}
        </nav>

        <div className="hidden lg:block">
          <Link href="/contact" className="btn-brand">
            Get a Free Quote
          </Link>
        </div>

        <button
          type="button"
          aria-label="Toggle menu"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-brand-line text-brand-ink lg:hidden"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <CloseIcon /> : <MenuIcon />}
        </button>
      </div>

      {open && (
        <div className="border-t border-brand-line bg-white lg:hidden">
          <nav className="section mx-auto flex max-w-7xl flex-col gap-1 py-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-xl px-3 py-2.5 text-sm font-medium text-brand-ink hover:bg-brand-mist"
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-2 border-t border-brand-line pt-3">
              {services.map((s) => (
                <Link
                  key={s.slug}
                  href={`/services/${s.slug}`}
                  className="block rounded-xl px-3 py-2 text-sm text-brand-slate hover:bg-brand-mist hover:text-brand-ink"
                >
                  {s.name}
                </Link>
              ))}
            </div>
            <Link href="/contact" className="btn-brand mt-3 justify-center">
              Get a Free Quote
            </Link>
          </nav>
        </div>
      )}
    </header>
  )
}
