import Link from 'next/link'
import { services } from '@/lib/services'
import { SERVICE_ICONS, ArrowRightIcon, CheckIcon } from '@/components/marketing/icons'

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden section pt-16 pb-20 sm:pt-24 sm:pb-28">
        <div
          className="pointer-events-none absolute -right-40 -top-40 h-[32rem] w-[32rem] rounded-full bg-brand-gradient opacity-10 blur-3xl"
          aria-hidden
        />
        <div className="relative mx-auto grid max-w-7xl items-center gap-16 lg:grid-cols-2">
          <div>
            <span className="eyebrow">Computer &amp; IT Specialists</span>
            <h1 className="mt-4 text-4xl font-bold leading-[1.1] tracking-tight text-brand-ink sm:text-5xl lg:text-6xl">
              IT support and repairs,{' '}
              <span className="brand-gradient-text">done properly.</span>
            </h1>
            <p className="mt-6 max-w-lg text-lg leading-relaxed text-brand-slate">
              Computer repair, printer support, home networks and WiFi troubleshooting for
              homes and small businesses — clear advice, careful work, and no jargon.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link href="/contact" className="btn-brand">
                Get a Free Quote <ArrowRightIcon />
              </Link>
              <Link href="/services" className="btn-brand-outline">
                View Our Services
              </Link>
            </div>

            <dl className="mt-14 grid grid-cols-2 gap-6 sm:grid-cols-4">
              {[
                'Friendly, jargon-free advice',
                'Remote & on-site support',
                'Transparent, upfront pricing',
                'Homes & small businesses',
              ].map((item) => (
                <div key={item} className="flex items-start gap-2">
                  <CheckIcon className="mt-0.5 shrink-0 text-brand-teal" size={18} />
                  <dt className="text-sm font-medium text-brand-ink">{item}</dt>
                </div>
              ))}
            </dl>
          </div>

          <div className="relative hidden lg:block">
            <div className="relative aspect-square w-full rounded-[2.5rem] bg-brand-gradient-soft p-10">
              <div className="flex h-full flex-col justify-between rounded-[1.75rem] border border-brand-line bg-white p-8 shadow-xl shadow-slate-900/5">
                <div className="flex items-center gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient text-white">
                    <SERVICE_ICONS.support size={22} />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-brand-ink">Support ticket #0231</p>
                    <p className="text-xs text-brand-slate">Home network — WiFi dead zone</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {['Diagnosis complete', 'Mesh point installed', 'Signal verified whole-home'].map((step) => (
                    <div key={step} className="flex items-center gap-2.5 rounded-xl bg-brand-mist px-4 py-3">
                      <CheckIcon className="text-brand-emerald" size={18} />
                      <span className="text-sm text-brand-ink">{step}</span>
                    </div>
                  ))}
                </div>
                <div className="rounded-xl bg-brand-navy px-5 py-4 text-white">
                  <p className="text-xs uppercase tracking-wide text-slate-400">Status</p>
                  <p className="mt-1 text-sm font-semibold text-brand-emerald">Ready for collection</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Services */}
      <section className="section bg-brand-mist py-20 sm:py-28">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-2xl">
            <span className="eyebrow">What we do</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-ink sm:text-4xl">
              Everything that keeps you connected and running smoothly
            </h2>
            <p className="mt-4 text-brand-slate">
              From a single stubborn laptop to a full home or office network, we cover it.
            </p>
          </div>

          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {services.map((service) => {
              const Icon = SERVICE_ICONS[service.icon]
              return (
                <Link
                  key={service.slug}
                  href={`/services/${service.slug}`}
                  className="group flex flex-col rounded-2xl border border-brand-line bg-white p-7 transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-900/5"
                >
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-gradient-soft text-brand-teal">
                    <Icon size={24} />
                  </span>
                  <h3 className="mt-5 text-lg font-semibold text-brand-ink">{service.name}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-brand-slate">{service.tagline}</p>
                  <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-brand-teal">
                    Learn more
                    <ArrowRightIcon size={16} className="transition-transform group-hover:translate-x-1" />
                  </span>
                </Link>
              )
            })}

            <Link
              href="/services"
              className="flex flex-col items-start justify-center rounded-2xl bg-brand-navy p-7 text-white transition-colors hover:bg-brand-ink"
            >
              <h3 className="text-lg font-semibold">See all services</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-300">
                Full details on everything we offer, plus what each visit typically involves.
              </p>
              <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-medium text-brand-emerald">
                View all <ArrowRightIcon size={16} />
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* Why us */}
      <section className="section py-20 sm:py-28">
        <div className="mx-auto grid max-w-7xl items-center gap-16 lg:grid-cols-2">
          <div>
            <span className="eyebrow">Why 404 Fixed</span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-ink sm:text-4xl">
              A more considered kind of IT support
            </h2>
            <p className="mt-4 text-brand-slate">
              We treat every home network the way we'd want ours treated, and every business
              system the way it deserves to be treated — properly diagnosed, properly fixed,
              properly explained.
            </p>

            <ul className="mt-8 space-y-5">
              {[
                {
                  title: 'Straightforward, honest advice',
                  body: 'We explain what’s wrong in plain English and only recommend work that’s genuinely needed.',
                },
                {
                  title: 'Careful with your data',
                  body: 'Your files and accounts are handled with the same care we’d want for our own.',
                },
                {
                  title: 'Remote or on-site, your choice',
                  body: 'Quick issues sorted remotely; hands-on jobs handled on-site at your home or office.',
                },
                {
                  title: 'Ongoing support, not just one-off fixes',
                  body: 'Support plans available for households and small businesses who want peace of mind year-round.',
                },
              ].map((item) => (
                <li key={item.title} className="flex gap-4">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-gradient-soft text-brand-teal">
                    <CheckIcon size={16} />
                  </span>
                  <div>
                    <p className="font-semibold text-brand-ink">{item.title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-brand-slate">{item.body}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-[2rem] bg-brand-navy p-10 text-white">
            <span className="eyebrow !text-brand-emerald">Our process</span>
            <h3 className="mt-3 text-2xl font-bold">How a typical job works</h3>
            <ol className="mt-8 space-y-6">
              {[
                ['Get in touch', 'Tell us what’s going on — by phone, form or email.'],
                ['We diagnose', 'We identify the real issue before recommending any work.'],
                ['We fix it', 'Remote or on-site, with clear pricing agreed up front.'],
                ['We follow up', 'Ongoing support available so problems don’t come back.'],
              ].map(([title, body], i) => (
                <li key={title} className="flex gap-5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10 text-sm font-bold">
                    {i + 1}
                  </span>
                  <div>
                    <p className="font-semibold">{title}</p>
                    <p className="mt-1 text-sm leading-relaxed text-slate-400">{body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section pb-20 sm:pb-28">
        <div className="mx-auto max-w-7xl overflow-hidden rounded-[2rem] bg-brand-gradient px-8 py-16 text-center sm:px-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Ready to get things working properly again?
          </h2>
          <p className="mx-auto mt-4 max-w-xl text-white/90">
            Tell us what's going on and we'll get back to you with straightforward advice and a
            clear quote — no obligation.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link href="/contact" className="rounded-full bg-white px-6 py-3 font-medium text-brand-ink transition-colors hover:bg-brand-mist">
              Get a Free Quote
            </Link>
            <Link href="/services" className="rounded-full border border-white/40 px-6 py-3 font-medium text-white transition-colors hover:bg-white/10">
              Explore Services
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
