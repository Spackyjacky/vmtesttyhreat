import type { Metadata } from 'next'
import ContactForm from '@/components/marketing/contact-form'
import { MapPinIcon, PhoneIcon, MailIcon, ClockIcon, ArrowRightIcon } from '@/components/marketing/icons'
import { CONTACT_EMAIL, SERVICE_AREA, SUMUP_BOOKING_URL } from '@/lib/site'

export const metadata: Metadata = {
  title: 'Contact',
  description: `Get in touch for IT support, network installs or WiFi help across ${SERVICE_AREA}.`,
  alternates: {
    canonical: '/contact',
  },
}

export default function ContactPage() {
  const phone = process.env.NEXT_PUBLIC_SHOP_PHONE ?? ''

  return (
    <section className="section py-16 sm:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <span className="eyebrow">Get in touch</span>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-brand-white sm:text-5xl">
            Let&apos;s get it sorted
          </h1>
          <p className="mt-5 text-lg text-brand-muted">
            Already know we cover you?{' '}
            <a href={SUMUP_BOOKING_URL} target="_blank" rel="noopener" className="text-brand-blue-bright hover:underline">
              Book straight on SumUp
            </a>
            . Otherwise, tell us what&apos;s going on below and we&apos;ll come back with clear,
            honest advice — no obligation.
          </p>
        </div>

        <div className="mt-14 grid gap-10 lg:grid-cols-[1fr_1.3fr]">
          <div className="space-y-4">
            <div className="rounded-2xl border border-brand-border p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                <MapPinIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-white">Service area</p>
              <p className="mt-1 text-sm text-brand-muted">Serving {SERVICE_AREA}</p>
            </div>

            {phone && (
              <div className="rounded-2xl border border-brand-border p-6">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                  <PhoneIcon size={20} />
                </span>
                <p className="mt-4 font-semibold text-brand-white">Call us</p>
                <a href={`tel:${phone.replace(/\s+/g, '')}`} className="mt-1 block text-sm text-brand-muted hover:text-brand-blue-bright">
                  {phone}
                </a>
              </div>
            )}

            <div className="rounded-2xl border border-brand-border p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                <MailIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-white">Email us</p>
              <a href={`mailto:${CONTACT_EMAIL}`} className="mt-1 block text-sm text-brand-muted hover:text-brand-blue-bright">
                {CONTACT_EMAIL}
              </a>
            </div>

            <div className="rounded-2xl border border-brand-border p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                <ClockIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-white">Opening hours</p>
              <p className="mt-1 text-sm text-brand-muted">Mon–Fri, 9am–5:30pm</p>
            </div>

            <a
              href={SUMUP_BOOKING_URL}
              target="_blank"
              rel="noopener"
              className="flex items-center justify-between gap-2 rounded-2xl border border-brand-border-strong bg-gradient-to-br from-brand-blue/[0.14] to-brand-blue/[0.03] p-6 text-brand-white hover:border-brand-blue-bright"
            >
              <span className="font-semibold">Book a visit on SumUp</span>
              <ArrowRightIcon size={18} className="text-brand-blue-bright" />
            </a>
          </div>

          <div className="rounded-[2rem] border border-brand-border bg-brand-surface p-8 sm:p-10">
            <ContactForm />
          </div>
        </div>
      </div>
    </section>
  )
}
