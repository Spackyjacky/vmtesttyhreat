import Link from 'next/link'
import type { Metadata } from 'next'
import { services } from '@/lib/services'
import { SERVICE_ICONS, ArrowRightIcon, CheckIcon } from '@/components/marketing/icons'

export const metadata: Metadata = {
  title: 'Services',
  description:
    'Computer repair, printer support, IT support, home network installation and WiFi troubleshooting.',
}

export default function ServicesPage() {
  return (
    <>
      <section className="section pb-16 pt-16 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow">Our Services</span>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-brand-ink sm:text-5xl">
            IT support and repairs for homes &amp; businesses
          </h1>
          <p className="mt-5 text-lg text-brand-slate">
            Five core services, one straightforward promise: honest diagnosis, careful work,
            and clear pricing before we start.
          </p>
        </div>
      </section>

      <section className="section pb-24">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          {services.map((service, index) => {
            const Icon = SERVICE_ICONS[service.icon]
            const reversed = index % 2 === 1
            return (
              <div
                key={service.slug}
                id={service.slug}
                className="grid gap-10 rounded-[2rem] border border-brand-line bg-white p-8 sm:p-12 lg:grid-cols-2 lg:items-center"
              >
                <div className={reversed ? 'lg:order-2' : ''}>
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white">
                    <Icon size={28} />
                  </span>
                  <h2 className="mt-6 text-2xl font-bold text-brand-ink">{service.name}</h2>
                  <p className="mt-3 text-brand-slate">{service.description}</p>
                  <Link
                    href={`/services/${service.slug}`}
                    className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-brand-teal"
                  >
                    Full details <ArrowRightIcon size={16} />
                  </Link>
                </div>

                <div className={`rounded-2xl bg-brand-mist p-7 ${reversed ? 'lg:order-1' : ''}`}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-slate">
                    We regularly help with
                  </p>
                  <ul className="mt-4 space-y-3">
                    {service.commonIssues.slice(0, 4).map((issue) => (
                      <li key={issue} className="flex items-start gap-2.5 text-sm text-brand-ink">
                        <CheckIcon className="mt-0.5 shrink-0 text-brand-teal" size={17} />
                        {issue}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      <section className="section pb-24">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-brand-navy px-8 py-14 text-center sm:px-16">
          <h2 className="text-2xl font-bold text-white sm:text-3xl">Not sure which service you need?</h2>
          <p className="mx-auto mt-3 max-w-xl text-slate-300">
            That's fine — describe the problem and we'll point you in the right direction.
          </p>
          <Link href="/contact" className="mt-7 inline-flex rounded-full bg-white px-6 py-3 font-medium text-brand-ink transition-colors hover:bg-brand-mist">
            Get in touch
          </Link>
        </div>
      </section>
    </>
  )
}
