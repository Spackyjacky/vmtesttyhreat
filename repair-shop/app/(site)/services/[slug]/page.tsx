import Link from 'next/link'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'
import { services, getServiceBySlug } from '@/lib/services'
import { SERVICE_ICONS, CheckIcon, TickIcon, ArrowRightIcon } from '@/components/marketing/icons'
import { SUMUP_BOOKING_URL } from '@/lib/site'

export function generateStaticParams() {
  return services.map((s) => ({ slug: s.slug }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  const service = getServiceBySlug(slug)
  if (!service) return {}
  return {
    title: service.name,
    description: service.description,
    alternates: {
      canonical: `/services/${service.slug}`,
    },
  }
}

export default async function ServiceDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const service = getServiceBySlug(slug)
  if (!service) notFound()

  const Icon = SERVICE_ICONS[service.icon]
  const otherServices = services.filter((s) => s.slug !== service.slug)

  return (
    <>
      <section className="section pb-16 pt-16 sm:pt-24">
        <div className="mx-auto max-w-4xl">
          <Link href="/services" className="text-sm font-medium text-brand-muted hover:text-brand-white">
            &larr; All services
          </Link>
          <div className="mt-6 flex items-center gap-4">
            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
              <Icon size={28} />
            </span>
            <div>
              <span className="eyebrow">{service.shortName}</span>
              <h1 className="mt-1 font-display text-3xl font-bold tracking-tight text-brand-white sm:text-4xl">
                {service.name}
              </h1>
            </div>
          </div>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-brand-muted">{service.description}</p>
          <div className="mt-8 flex flex-wrap gap-4">
            <a className="btn-brand" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book {service.shortName} <ArrowRightIcon />
            </a>
            <Link href="/services" className="btn-brand-outline">
              Compare all services
            </Link>
          </div>
        </div>
      </section>

      <section className="section pb-20">
        <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-2">
          <div className="rounded-2xl border border-brand-border p-8">
            <h2 className="text-lg font-semibold text-brand-white">What&apos;s included</h2>
            <ul className="mt-5 space-y-3.5">
              {service.highlights.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-brand-white">
                  <CheckIcon className="mt-0.5 shrink-0 text-brand-blue-bright" size={18} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-2xl bg-brand-bg-alt p-8">
            <h2 className="text-lg font-semibold text-brand-white">Common problems we fix</h2>
            <ul className="mt-5 space-y-3.5">
              {service.commonIssues.map((item) => (
                <li key={item} className="flex items-start gap-2.5 text-sm text-brand-white">
                  <TickIcon className="mt-0.5 shrink-0 text-brand-green" size={16} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="section pb-24">
        <div className="mx-auto max-w-4xl">
          <h2 className="text-xl font-bold text-brand-white">Other services</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {otherServices.map((s) => {
              const OtherIcon = SERVICE_ICONS[s.icon]
              return (
                <Link
                  key={s.slug}
                  href={`/services/${s.slug}`}
                  className="group flex items-center gap-4 rounded-xl border border-brand-border p-5 transition-colors hover:border-brand-blue-bright"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                    <OtherIcon size={20} />
                  </span>
                  <span className="text-sm font-medium text-brand-white">{s.name}</span>
                  <ArrowRightIcon size={16} className="ml-auto text-brand-muted transition-transform group-hover:translate-x-1" />
                </Link>
              )
            })}
          </div>
        </div>
      </section>
    </>
  )
}
