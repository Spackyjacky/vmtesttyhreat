'use client'

import { useEffect, useRef, useState } from 'react'
import { COVERED_CODES, CONTACT_EMAIL, SUMUP_BOOKING_URL } from '@/lib/site'
import { CheckIcon, AlertIcon, ArrowRightIcon } from './icons'

const UK_POSTCODE_RE = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}$/i

function outwardCode(raw: string) {
  const clean = raw.toUpperCase().replace(/\s+/g, '')
  if (clean.length < 5) return clean
  return clean.slice(0, clean.length - 3)
}

type Status = 'idle' | 'covered' | 'not-covered'

export default function PostcodeChecker() {
  const [value, setValue] = useState('')
  const [lines, setLines] = useState<string[]>([])
  const [status, setStatus] = useState<Status>('idle')
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])

  useEffect(() => {
    return () => {
      timers.current.forEach(clearTimeout)
    }
  }, [])

  function typeLines(newLines: string[], onDone?: () => void) {
    timers.current.forEach(clearTimeout)
    timers.current = []
    setLines([])

    const reduceMotion =
      typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const delay = reduceMotion ? 0 : 260

    newLines.forEach((line, i) => {
      const t = setTimeout(
        () => {
          setLines((prev) => [...prev, line])
          if (i === newLines.length - 1 && onDone) {
            const t2 = setTimeout(onDone, reduceMotion ? 0 : 200)
            timers.current.push(t2)
          }
        },
        reduceMotion ? 0 : i * delay
      )
      timers.current.push(t)
    })
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const raw = value.trim()
    setStatus('idle')

    if (!raw) {
      typeLines(['Enter a postcode to check coverage.'])
      return
    }

    if (!UK_POSTCODE_RE.test(raw)) {
      typeLines([`resolving "${raw}"...`, `that doesn't look like a valid UK postcode. Try e.g. CF10 2AB.`])
      return
    }

    const outward = outwardCode(raw)
    const covered = COVERED_CODES.includes(outward)

    typeLines(
      [
        `resolving ${raw.toUpperCase()}...`,
        `checking against Cardiff & Penarth service area...`,
        `district ${outward} — ${covered ? 'CONNECTION ESTABLISHED' : 'OUT OF RANGE'}`,
      ],
      () => setStatus(covered ? 'covered' : 'not-covered')
    )
  }

  return (
    <div className="relative overflow-hidden rounded-[20px] border border-brand-border-strong bg-gradient-to-b from-brand-surface to-brand-bg-alt p-6 shadow-[0_30px_60px_-30px_rgba(0,0,0,0.7)]">
      <div className="pointer-events-none absolute -right-[30%] -top-[40%] h-[140%] w-[60%] bg-brand-glow" aria-hidden="true" />

      <div className="relative mb-4 flex items-center justify-between">
        <span className="font-mono text-xs uppercase tracking-wide text-brand-muted">Coverage check</span>
        <div className="flex gap-1.5">
          <span className="h-[9px] w-[9px] rounded-full border border-brand-border-strong bg-brand-surface-2" />
          <span className="h-[9px] w-[9px] rounded-full border border-brand-border-strong bg-brand-surface-2" />
          <span className="h-[9px] w-[9px] rounded-full border border-brand-border-strong bg-brand-surface-2" />
        </div>
      </div>

      <h2 className="relative mb-1.5 font-display text-xl font-semibold text-brand-white">Are we on your network?</h2>
      <p className="relative mb-5 text-sm text-brand-muted">
        Pop in your postcode — we&apos;ll check it against our Cardiff &amp; Penarth service area.
      </p>

      <form onSubmit={handleSubmit} className="relative mb-4 flex gap-2.5">
        <label htmlFor="postcodeInput" className="sr-only">
          Enter your postcode
        </label>
        <input
          type="text"
          id="postcodeInput"
          name="postcode"
          value={value}
          onChange={(e) => setValue(e.target.value.toUpperCase())}
          placeholder="e.g. CF10 2AB"
          autoComplete="postal-code"
          inputMode="text"
          className="min-w-0 flex-1 rounded-[9px] border border-brand-border-strong bg-brand-bg px-3.5 py-[13px] font-mono text-base uppercase tracking-wide text-brand-white placeholder:font-sans placeholder:normal-case placeholder:tracking-normal placeholder:text-brand-muted-2 focus:border-brand-blue-bright focus:outline-none"
        />
        <button type="submit" className="btn-brand">
          Check
        </button>
      </form>

      <div
        className="relative min-h-[118px] rounded-[10px] border border-brand-border bg-brand-bg p-4 font-mono text-sm text-brand-muted"
        aria-live="polite"
      >
        {lines.length === 0 ? (
          <p className="text-brand-muted-2">
            Waiting for postcode
            <span className="cursor-blink" />
          </p>
        ) : (
          lines.map((line, i) => (
            <p key={i} className="terminal-line mb-1.5 last:mb-0">
              <span className="mr-1.5 text-brand-blue-bright">&gt;</span>
              {line}
            </p>
          ))
        )}
      </div>

      {status === 'covered' && (
        <div className="relative mt-4 flex items-start gap-3 rounded-[10px] border border-brand-green/40 bg-brand-green/10 p-4">
          <CheckIcon className="mt-0.5 shrink-0 text-brand-green" size={20} />
          <div>
            <p className="mb-1 text-[0.98rem] font-semibold text-brand-white">Good news — we cover this area</p>
            <p className="mb-3 text-sm text-brand-muted">
              You&apos;re inside the 404 Fixed service area. Book a visit and we&apos;ll get you sorted.
            </p>
            <a className="btn-brand inline-flex text-sm" href={SUMUP_BOOKING_URL} target="_blank" rel="noopener">
              Book on SumUp <ArrowRightIcon size={14} />
            </a>
          </div>
        </div>
      )}

      {status === 'not-covered' && (
        <div className="relative mt-4 flex items-start gap-3 rounded-[10px] border border-brand-amber/40 bg-brand-amber/10 p-4">
          <AlertIcon className="mt-0.5 shrink-0 text-brand-amber" size={20} />
          <div>
            <p className="mb-1 text-[0.98rem] font-semibold text-brand-white">Outside our current service area</p>
            <p className="mb-3 text-sm text-brand-muted">
              We&apos;re only taking on jobs across Cardiff &amp; Penarth right now. Get in touch anyway and
              we&apos;ll let you know if that changes.
            </p>
            <a className="btn-brand-outline inline-flex text-sm" href={`mailto:${CONTACT_EMAIL}?subject=Coverage%20enquiry`}>
              Contact us
            </a>
          </div>
        </div>
      )}
    </div>
  )
}
