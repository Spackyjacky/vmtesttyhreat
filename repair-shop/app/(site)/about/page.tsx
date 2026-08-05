import Link from 'next/link'
import type { Metadata } from 'next'
import { CheckIcon, ArrowRightIcon } from '@/components/marketing/icons'

export const metadata: Metadata = {
  title: 'About',
  description: 'Straightforward, professional computer repair and IT support.',
}

const VALUES = [
  {
    title: 'Honesty first',
    body: 'We diagnose before we quote, and we only recommend work that’s genuinely needed — never more.',
  },
  {
    title: 'Plain English',
    body: 'No jargon, no scare tactics. Just a clear explanation of what’s wrong and what it takes to fix it.',
  },
  {
    title: 'Care with your data',
    body: 'Your files, accounts and devices are handled with the same discretion and care we’d want for our own.',
  },
  {
    title: 'Built to last',
    body: 'Fixes and installs are done properly the first time, so the same problem doesn’t come back next month.',
  },
]

export default function AboutPage() {
  return (
    <>
      <section className="section pb-16 pt-16 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow">About 404 Fixed</span>
          <h1 className="mt-3 text-4xl font-bold tracking-tight text-brand-ink sm:text-5xl">
            IT support, without the fuss
          </h1>
          <p className="mt-5 text-lg text-brand-slate">
            404 Fixed provides computer repair, printer support and IT support to homes and
            small businesses — with the kind of clear, considered service you'd expect from a
            trusted local specialist.
          </p>
        </div>
      </section>

      <section className="section pb-20">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-2 lg:items-center">
          <div className="rounded-[2rem] bg-brand-gradient-soft p-10">
            <div className="rounded-[1.5rem] border border-brand-line bg-white p-8">
              <p className="text-sm font-semibold uppercase tracking-wide text-brand-teal">Our focus</p>
              <p className="mt-4 text-xl font-semibold leading-snug text-brand-ink">
                Computers, printers, networks and WiFi — done properly, explained clearly.
              </p>
              <p className="mt-4 text-sm leading-relaxed text-brand-slate">
                We work with individuals and small businesses who want technology that just
                works, and a straightforward point of contact when it doesn't.
              </p>
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-bold tracking-tight text-brand-ink">What we stand for</h2>
            <p className="mt-3 text-brand-slate">
              A handful of principles guide every job, whether it's a quick fix or a full
              network install.
            </p>
            <div className="mt-8 grid gap-6 sm:grid-cols-2">
              {VALUES.map((value) => (
                <div key={value.title} className="rounded-2xl border border-brand-line p-6">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-gradient-soft text-brand-teal">
                    <CheckIcon size={18} />
                  </span>
                  <p className="mt-4 font-semibold text-brand-ink">{value.title}</p>
                  <p className="mt-2 text-sm leading-relaxed text-brand-slate">{value.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section pb-24">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-brand-navy px-8 py-16 text-center sm:px-16">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">Let's sort it out</h2>
          <p className="mx-auto mt-4 max-w-xl text-slate-300">
            Get in touch and tell us what's going on — we'll come back with clear advice and a
            straightforward quote.
          </p>
          <Link href="/contact" className="mt-8 inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 font-medium text-brand-ink transition-colors hover:bg-brand-mist">
            Contact us <ArrowRightIcon />
          </Link>
        </div>
      </section>
    </>
  )
}
