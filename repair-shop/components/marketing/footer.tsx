import Link from 'next/link'
import Logo from './logo'
import { services } from '@/lib/services'
import { MapPinIcon, PhoneIcon, MailIcon, ClockIcon } from './icons'

export default function Footer() {
  const phone = process.env.NEXT_PUBLIC_SHOP_PHONE ?? ''
  const email = process.env.NEXT_PUBLIC_SHOP_EMAIL ?? 'hello@404fixed.co.uk'
  const area = process.env.NEXT_PUBLIC_SHOP_AREA ?? 'Your Area'

  return (
    <footer className="bg-brand-navy text-slate-300">
      <div className="section mx-auto max-w-7xl py-16">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_1fr_1fr_1.2fr]">
          <div>
            <Logo dark tagline />
            <p className="mt-5 max-w-sm text-sm leading-relaxed text-slate-400">
              Considered, professional computer repair and IT support — for homes and
              businesses that expect it done properly, the first time.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-white">Services</h3>
            <ul className="mt-4 space-y-2.5 text-sm">
              {services.map((s) => (
                <li key={s.slug}>
                  <Link href={`/services/${s.slug}`} className="text-slate-400 transition-colors hover:text-white">
                    {s.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-white">Company</h3>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li><Link href="/about" className="text-slate-400 transition-colors hover:text-white">About Us</Link></li>
              <li><Link href="/services" className="text-slate-400 transition-colors hover:text-white">All Services</Link></li>
              <li><Link href="/contact" className="text-slate-400 transition-colors hover:text-white">Contact</Link></li>
              <li><Link href="/login" className="text-slate-400 transition-colors hover:text-white">Staff Login</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-white">Get in touch</h3>
            <ul className="mt-4 space-y-3 text-sm text-slate-400">
              <li className="flex items-start gap-2.5">
                <MapPinIcon className="mt-0.5 shrink-0 text-brand-teal" size={18} />
                <span>Serving {area} &amp; surrounding areas</span>
              </li>
              {phone && (
                <li className="flex items-start gap-2.5">
                  <PhoneIcon className="mt-0.5 shrink-0 text-brand-teal" size={18} />
                  <a href={`tel:${phone.replace(/\s+/g, '')}`} className="hover:text-white">{phone}</a>
                </li>
              )}
              <li className="flex items-start gap-2.5">
                <MailIcon className="mt-0.5 shrink-0 text-brand-teal" size={18} />
                <a href={`mailto:${email}`} className="hover:text-white">{email}</a>
              </li>
              <li className="flex items-start gap-2.5">
                <ClockIcon className="mt-0.5 shrink-0 text-brand-teal" size={18} />
                <span>Mon–Fri, 9am–5:30pm</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="section mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 py-6 text-xs text-slate-500 sm:flex-row">
          <p>&copy; {new Date().getFullYear()} 404 Fixed. All rights reserved.</p>
          <p>Computer repair &amp; IT support you can rely on.</p>
        </div>
      </div>
    </footer>
  )
}
