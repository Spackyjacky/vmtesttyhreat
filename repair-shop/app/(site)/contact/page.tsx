import type { Metadata } from 'next'
import ContactForm from '@/components/marketing/contact-form'
import { MapPinIcon, PhoneIcon, MailIcon, ClockIcon } from '@/components/marketing/icons'

export const metadata: Metadata = {
  title: 'Contact',
  description: 'Get in touch for computer repair, printer support, IT support or networking help.',
}

export default function ContactPage() {
  const phone = process.env.NEXT_PUBLIC_SHOP_PHONE ?? ''
  const email = process.env.NEXT_PUBLIC_SHOP_EMAIL ?? 'hello@404fixed.co.uk'
  const area = process.env.NEXT_PUBLIC_SHOP_AREA ?? 'Your Area'

  return (
    <section className="section py-16 sm:py-24">
      <div className="mx-auto max-w-6xl">
        <div className="max-w-2xl">
          <span className="eyebrow">Get in touch</span>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-brand-ink sm:text-5xl">
            Let's get it sorted
          </h1>
          <p className="mt-5 text-lg text-brand-slate">
            Tell us what's going on and we'll come back with clear, honest advice — no
            obligation.
          </p>
        </div>

        <div className="mt-14 grid gap-10 lg:grid-cols-[1fr_1.3fr]">
          <div className="space-y-4">
            <div className="rounded-2xl border border-brand-line p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft text-brand-teal">
                <MapPinIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-ink">Service area</p>
              <p className="mt-1 text-sm text-brand-slate">Serving {area} &amp; surrounding areas</p>
            </div>

            {phone && (
              <div className="rounded-2xl border border-brand-line p-6">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft text-brand-teal">
                  <PhoneIcon size={20} />
                </span>
                <p className="mt-4 font-semibold text-brand-ink">Call us</p>
                <a href={`tel:${phone.replace(/\s+/g, '')}`} className="mt-1 block text-sm text-brand-slate hover:text-brand-teal">
                  {phone}
                </a>
              </div>
            )}

            <div className="rounded-2xl border border-brand-line p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft text-brand-teal">
                <MailIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-ink">Email us</p>
              <a href={`mailto:${email}`} className="mt-1 block text-sm text-brand-slate hover:text-brand-teal">
                {email}
              </a>
            </div>

            <div className="rounded-2xl border border-brand-line p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient-soft text-brand-teal">
                <ClockIcon size={20} />
              </span>
              <p className="mt-4 font-semibold text-brand-ink">Opening hours</p>
              <p className="mt-1 text-sm text-brand-slate">Mon–Fri, 9am–5:30pm</p>
            </div>
          </div>

          <div className="rounded-[2rem] border border-brand-line bg-white p-8 sm:p-10">
            <ContactForm />
          </div>
        </div>
      </div>
    </section>
  )
}
