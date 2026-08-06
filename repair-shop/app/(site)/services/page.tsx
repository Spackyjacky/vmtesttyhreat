import Link from 'next/link'
import type { Metadata } from 'next'
import { services } from '@/lib/services'
import { SERVICE_ICONS, ArrowRightIcon, TickIcon } from '@/components/marketing/icons'
import { SUMUP_BOOKING_URL } from '@/lib/site'

export const metadata: Metadata = {
  title: 'Services',
  description: 'IT support, network installs and WiFi help across Cardiff & Penarth.',
}

export default function ServicesPage() {
  return (
    <>
      <section className="section pb-16 pt-16 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow">Our Services</span>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-brand-white sm:text-5xl">
            Three problems, one call.
          </h1>
          <p className="mt-5 text-lg text-brand-muted">
            One straightforward promise: honest diagnosis, careful work, and clear pricing before
            we start.
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
                className="grid gap-10 rounded-[2rem] border border-brand-border bg-brand-surface p-8 sm:p-12 lg:grid-cols-2 lg:items-center"
              >
                <div className={reversed ? 'lg:order-2' : ''}>
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                    <Icon size={28} />
                  </span>
                  <h2 className="mt-6 font-display text-2xl font-bold text-brand-white">{service.name}</h2>
                  <p className="mt-3 text-brand-muted">{service.description}</p>
                  <div className="mt-6 flex flex-wrap gap-4">
                    <a
                      href={SUMUP_BOOKING_URL}
                      target="_blank"
                      rel="noopener"
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-blue-bright hover:underline"
                    >
                      Book {service.shortName} <ArrowRightIcon size={16} />
                    </a>
                    <Link
                      href={`/services/${service.slug}`}
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-muted hover:text-brand-white"
                    >
                      Full details <ArrowRightIcon size={16} />
                    </Link>
                  </div>
                </div>

                <div className={`rounded-2xl bg-brand-bg-alt p-7 ${reversed ? 'lg:order-1' : ''}`}>
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-muted">We regularly help with</p>
                  <ul className="mt-4 space-y-3">
                    {service.commonIssues.slice(0, 4).map((issue) => (
                      <li key={issue} className="flex items-start gap-2.5 text-sm text-brand-white">
                        <TickIcon className="mt-0.5 shrink-0 text-brand-green" size={16} />
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
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] border border-brand-border-strong bg-brand-bg-alt px-8 py-14 text-center sm:px-16">
          <h2 className="font-display text-2xl font-bold text-brand-white sm:text-3xl">Not sure which service you need?</h2>
          <p className="mx-auto mt-3 max-w-xl text-brand-muted">
            That&apos;s fine — describe the problem and we&apos;ll point you in the right direction.
          </p>
          <Link href="/contact" className="btn-brand mt-7 inline-flex">
            Get in touch
          </Link>
        </div>
      </section>
    </>
  )
}
