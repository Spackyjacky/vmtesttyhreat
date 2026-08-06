import Link from 'next/link'
import type { Metadata } from 'next'
import { CheckIcon, ArrowRightIcon } from '@/components/marketing/icons'
import { SERVICE_AREA, SUMUP_BOOKING_URL } from '@/lib/site'

export const metadata: Metadata = {
  title: 'How it works',
  description: `IT problems don't wait, neither do we. IT support, network installs and WiFi help across ${SERVICE_AREA}.`,
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

const STEPS = [
  ['01', 'Check & book', 'Confirm we cover your postcode, then grab a slot that works for you on SumUp.'],
  ['02', 'We diagnose', 'We get to the root of the problem on-site or remotely — no guesswork, no unnecessary parts.'],
  ['03', 'We fix it', 'Straight answers, a proper fix, and advice to stop it happening again.'],
]

export default function AboutPage() {
  return (
    <>
      <section className="section pb-16 pt-16 sm:pt-24">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow">About 404 Fixed</span>
          <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-brand-white sm:text-5xl">
            IT problems don&apos;t wait. Neither do we.
          </h1>
          <p className="mt-5 text-lg text-brand-muted">
            404 Fixed delivers IT support, network installs and WiFi help to homes and small
            businesses across {SERVICE_AREA} — with the kind of clear, considered service you&apos;d
            expect from a trusted local specialist.
          </p>
        </div>
      </section>

      <section className="section pb-20">
        <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-2 lg:items-center">
          <div className="rounded-[2rem] border border-brand-border-strong bg-gradient-to-br from-brand-blue/[0.14] to-brand-blue/[0.03] p-10">
            <div className="rounded-[1.5rem] border border-brand-border bg-brand-surface p-8">
              <p className="text-sm font-semibold uppercase tracking-wide text-brand-blue-bright">Our focus</p>
              <p className="mt-4 text-xl font-semibold leading-snug text-brand-white">
                IT support, network installs and WiFi help — done properly, explained clearly.
              </p>
              <p className="mt-4 text-sm leading-relaxed text-brand-muted">
                We work with individuals and small businesses who want technology that just works,
                and a straightforward point of contact when it doesn&apos;t.
              </p>
            </div>
          </div>

          <div>
            <h2 className="font-display text-2xl font-bold tracking-tight text-brand-white">What we stand for</h2>
            <p className="mt-3 text-brand-muted">
              A handful of principles guide every job, whether it&apos;s a quick fix or a full
              network install.
            </p>
            <div className="mt-8 grid gap-6 sm:grid-cols-2">
              {VALUES.map((value) => (
                <div key={value.title} className="rounded-2xl border border-brand-border p-6">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full border border-brand-border-strong bg-brand-blue/10 text-brand-blue-bright">
                    <CheckIcon size={18} />
                  </span>
                  <p className="mt-4 font-semibold text-brand-white">{value.title}</p>
                  <p className="mt-2 text-sm leading-relaxed text-brand-muted">{value.body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section border-y border-brand-border bg-brand-bg-alt py-20">
        <div className="mx-auto max-w-6xl">
          <p className="eyebrow mb-3 text-center">How it works</p>
          <h2 className="mb-12 text-center font-display text-3xl font-bold tracking-tight text-brand-white sm:text-4xl">
            Sorted in three steps.
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {STEPS.map(([num, title, body]) => (
              <div key={num}>
                <div className="mb-[18px] flex h-[38px] w-[38px] items-center justify-center rounded-[10px] border border-brand-border-strong bg-brand-surface font-display text-[0.95rem] font-bold text-brand-blue-bright">
                  {num}
                </div>
                <h3 className="mb-2 font-display text-[1.1rem] font-semibold text-brand-white">{title}</h3>
                <p className="text-sm text-brand-muted">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="section pb-24 pt-24">
        <div className="mx-auto max-w-6xl overflow-hidden rounded-[2rem] border border-brand-border-strong bg-gradient-to-br from-brand-blue/[0.14] to-brand-blue/[0.03] px-8 py-16 text-center sm:px-16">
          <h2 className="font-display text-3xl font-bold text-brand-white sm:text-4xl">Let&apos;s sort it out</h2>
          <p className="mx-auto mt-4 max-w-xl text-brand-muted">
            Check your postcode, pick a slot, and let&apos;s get it 404 Fixed.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3.5">
            <a className="btn-brand" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book on SumUp <ArrowRightIcon />
            </a>
            <Link href="/contact" className="btn-brand-outline">
              Contact us
            </Link>
          </div>
        </div>
      </section>
    </>
  )
}
