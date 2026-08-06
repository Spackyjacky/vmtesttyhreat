import Link from 'next/link'
import { services } from '@/lib/services'
import { SERVICE_ICONS, ArrowRightIcon, ClockIcon, ShieldIcon, ITSupportIcon, WifiIcon, TickIcon } from '@/components/marketing/icons'
import PostcodeChecker from '@/components/marketing/postcode-checker'
import { COVERED_DISTRICTS, SUMUP_BOOKING_URL } from '@/lib/site'

const TRUST_ITEMS = [
  { icon: ClockIcon, label: 'Fast response' },
  { icon: ShieldIcon, label: 'Expert support' },
  { icon: ITSupportIcon, label: 'Business & home' },
  { icon: WifiIcon, label: 'Cardiff-based' },
]

const STEPS = [
  {
    num: '01',
    title: 'Check & book',
    body: 'Confirm we cover your postcode above, then grab a slot that works for you on SumUp.',
  },
  {
    num: '02',
    title: 'We diagnose',
    body: 'We get to the root of the problem on-site or remotely — no guesswork, no unnecessary parts.',
  },
  {
    num: '03',
    title: 'We fix it',
    body: 'Straight answers, a proper fix, and advice to stop it happening again.',
  },
]

const FAQS = [
  {
    q: 'Do you cover areas outside Cardiff & Penarth?',
    a: 'Not right now — we’re focused on doing right by customers across Cardiff and Penarth postcodes. If you’re just outside, drop us a message and we’ll let you know if that changes.',
  },
  {
    q: 'Do you work with businesses as well as homes?',
    a: 'Yes — from home offices to small business networks, we handle both. Network installs and ongoing IT support are common for business customers.',
  },
  {
    q: 'How do I book a visit?',
    a: 'Once you’ve confirmed we cover your postcode, hit any "Book now" button on this page — it takes you straight to our SumUp booking page to pick a time that suits you.',
  },
  {
    q: 'Can you help remotely?',
    a: 'For a lot of IT support issues, yes. Network installs and WiFi troubleshooting usually need an on-site visit — we’ll advise what’s best when you book.',
  },
]

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="section pb-16 pt-[88px] sm:pb-16">
        <div className="mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <span className="mb-[22px] inline-flex items-center gap-2 rounded-full border border-brand-border-strong bg-brand-blue/10 px-3 py-1.5 font-mono text-[0.78rem] uppercase tracking-[0.06em] text-brand-blue-bright">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-green shadow-[0_0_8px_theme(colors.brand.green)]" />
              Serving Cardiff &amp; Penarth
            </span>
            <h1 className="mb-5 font-display text-[clamp(2.2rem,4.2vw,3.4rem)] font-bold leading-[1.06] tracking-[-0.01em] text-brand-white">
              IT problems don&apos;t wait. <span className="text-brand-blue-bright">Neither do we.</span>
            </h1>
            <p className="mb-[30px] max-w-[46ch] text-[1.08rem] leading-relaxed text-brand-muted">
              404 Fixed delivers fast, no-nonsense IT support, network installs and WiFi
              troubleshooting for homes and businesses. Enter your postcode and see if we&apos;re
              already on your network.
            </p>
            <div className="mb-9 flex flex-wrap items-center gap-3.5">
              <a className="btn-brand" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
                Book a visit <ArrowRightIcon size={16} />
              </a>
              <a className="btn-brand-outline" href="#checker-card">
                Check my postcode
              </a>
            </div>
            <div className="flex flex-wrap gap-x-7 gap-y-5 border-t border-brand-border pt-6">
              {TRUST_ITEMS.map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-2 text-sm text-brand-muted">
                  <Icon className="shrink-0 text-brand-blue-bright" size={16} />
                  {label}
                </div>
              ))}
            </div>
          </div>

          <div id="checker-card">
            <PostcodeChecker />
          </div>
        </div>
      </section>

      {/* Services */}
      <section className="section border-y border-brand-border bg-brand-bg-alt py-[88px]" id="services">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-[640px]">
            <p className="eyebrow mb-3">What we do</p>
            <h2 className="mb-3.5 font-display text-[clamp(1.7rem,2.8vw,2.3rem)] font-bold tracking-[-0.01em] text-brand-white">
              Three problems, one call.
            </h2>
            <p className="text-[1.02rem] text-brand-muted">
              From a slow office network to a WiFi dead zone in the back bedroom — we diagnose it
              properly and fix it right the first time.
            </p>
          </div>

          <div className="grid gap-[22px] md:grid-cols-3">
            {services.map((service) => {
              const Icon = SERVICE_ICONS[service.icon]
              return (
                <div
                  key={service.slug}
                  className="rounded-2xl border border-brand-border bg-brand-surface p-7 transition-all hover:-translate-y-[3px] hover:border-brand-border-strong"
                >
                  <span className="mb-[18px] flex h-11 w-11 items-center justify-center rounded-[11px] border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                    <Icon size={22} />
                  </span>
                  <h3 className="mb-2.5 font-display text-[1.15rem] font-semibold text-brand-white">{service.name}</h3>
                  <p className="mb-[18px] text-sm text-brand-muted">{service.tagline}</p>
                  <div className="flex flex-wrap gap-3">
                    <a
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-blue-bright hover:underline"
                      href={SUMUP_BOOKING_URL}
                      target="_blank"
                      rel="noopener"
                    >
                      Book {service.shortName} <ArrowRightIcon size={14} />
                    </a>
                    <Link
                      href={`/services/${service.slug}`}
                      className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-muted hover:text-brand-white"
                    >
                      Learn more <ArrowRightIcon size={14} />
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="section py-[88px]" id="how">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-[640px]">
            <p className="eyebrow mb-3">The process</p>
            <h2 className="font-display text-[clamp(1.7rem,2.8vw,2.3rem)] font-bold tracking-[-0.01em] text-brand-white">
              Sorted in three steps.
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            {STEPS.map((step) => (
              <div key={step.num}>
                <div className="mb-[18px] flex h-[38px] w-[38px] items-center justify-center rounded-[10px] border border-brand-border-strong bg-brand-surface font-display text-[0.95rem] font-bold text-brand-blue-bright">
                  {step.num}
                </div>
                <h3 className="mb-2 font-display text-[1.1rem] font-semibold text-brand-white">{step.title}</h3>
                <p className="text-sm text-brand-muted">{step.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Coverage */}
      <section className="section border-y border-brand-border bg-brand-bg-alt py-[88px]" id="coverage">
        <div className="mx-auto grid max-w-7xl items-center gap-14 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="eyebrow mb-3">Service area</p>
            <h2 className="mb-3.5 font-display text-[clamp(1.7rem,2.8vw,2.3rem)] font-bold tracking-[-0.01em] text-brand-white">
              Cardiff &amp; Penarth, covered.
            </h2>
            <p className="text-[1.02rem] text-brand-muted">
              We currently take on jobs across these postcode districts. Not sure? Use the checker
              at the top of the page.
            </p>
            <a className="btn-brand mt-7 inline-flex" href="#checker-card">
              Check my postcode
            </a>
          </div>
          <div className="flex flex-wrap gap-2.5">
            {COVERED_DISTRICTS.map((d) => (
              <span
                key={d.code}
                className="flex items-center gap-2 rounded-[9px] border border-brand-border-strong bg-brand-surface px-3.5 py-2.5 font-mono text-[0.84rem] text-brand-white"
              >
                <TickIcon className="text-brand-green" size={14} />
                <b className="text-brand-blue-bright">{d.code}</b>&nbsp;{d.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Mid banner */}
      <section className="section py-[88px]">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-wrap items-center justify-between gap-8 rounded-[20px] border border-brand-border-strong bg-gradient-to-br from-brand-blue/[0.14] to-brand-blue/[0.03] p-11">
            <div>
              <h3 className="mb-2 font-display text-2xl font-bold text-brand-white">WiFi giving you grief right now?</h3>
              <p className="max-w-[44ch] text-brand-muted">
                Book a visit today and we&apos;ll have you back online with a signal that actually
                reaches the whole house.
              </p>
            </div>
            <a className="btn-brand shrink-0" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book now
            </a>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="section py-[88px]" id="faq">
        <div className="mx-auto max-w-7xl">
          <div className="mb-12 max-w-[640px]">
            <p className="eyebrow mb-3">Questions</p>
            <h2 className="font-display text-[clamp(1.7rem,2.8vw,2.3rem)] font-bold tracking-[-0.01em] text-brand-white">
              Good to know.
            </h2>
          </div>
          <div className="flex flex-col overflow-hidden rounded-2xl border border-brand-border">
            {FAQS.map((faq, i) => (
              <details key={faq.q} className={`group bg-brand-surface ${i !== FAQS.length - 1 ? 'border-b border-brand-border' : ''}`}>
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-6 py-5 text-[0.98rem] font-semibold text-brand-white [&::-webkit-details-marker]:hidden">
                  {faq.q}
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth={2.2}
                    strokeLinecap="round"
                    className="h-[18px] w-[18px] shrink-0 text-brand-blue-bright transition-transform group-open:rotate-45"
                  >
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                </summary>
                <p className="max-w-[64ch] px-6 pb-5 text-sm text-brand-muted">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="section pb-24 pt-20 text-center">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-4 font-display text-[clamp(1.9rem,3.4vw,2.6rem)] font-bold text-brand-white">Ready when you are.</h2>
          <p className="mx-auto mb-8 max-w-[52ch] text-[1.02rem] text-brand-muted">
            Check your postcode, pick a slot, and let&apos;s get it 404 Fixed.
          </p>
          <div className="flex flex-wrap justify-center gap-3.5">
            <a className="btn-brand" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book on SumUp <ArrowRightIcon size={16} />
            </a>
            <a className="btn-brand-outline" href="#checker-card">
              Check my postcode
            </a>
          </div>
        </div>
      </section>
    </>
  )
}
