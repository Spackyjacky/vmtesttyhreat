'use client'

import { useState } from 'react'
import { services } from '@/lib/services'
import { CheckIcon } from './icons'

const fieldClass =
  'w-full rounded-[9px] border border-brand-border-strong bg-brand-bg px-4 py-3 text-sm text-brand-white placeholder:text-brand-muted-2 focus:border-brand-blue-bright focus:outline-none focus:ring-2 focus:ring-brand-blue/20'

export default function ContactForm() {
  const [status, setStatus] = useState<'idle' | 'submitting' | 'sent' | 'error'>('idle')
  const [errorMessage, setErrorMessage] = useState('')

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setStatus('submitting')

    const form = new FormData(e.currentTarget)
    const payload = {
      name: form.get('name'),
      email: form.get('email'),
      phone: form.get('phone'),
      service: form.get('service'),
      message: form.get('message'),
      company: form.get('company'),
    }

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => null)
      if (!res.ok || !data?.ok) {
        throw new Error(data?.error || 'Failed to send')
      }
      setStatus('sent')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : '')
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <div className="rounded-2xl border border-brand-border bg-brand-bg-alt p-8 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-gradient text-white">
          <CheckIcon size={22} />
        </span>
        <h3 className="mt-4 text-lg font-semibold text-brand-white">Thanks — message sent</h3>
        <p className="mt-2 text-sm text-brand-muted">
          We&apos;ll get back to you as soon as we can, usually within one working day.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Honeypot — hidden from real users, catches simple bots that fill every field */}
      <div className="absolute left-[-9999px] top-auto h-0 w-0 overflow-hidden" aria-hidden="true">
        <label htmlFor="company">Company</label>
        <input id="company" name="company" type="text" tabIndex={-1} autoComplete="off" />
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-brand-white">
            Name
          </label>
          <input id="name" name="name" required className={fieldClass} placeholder="Your name" />
        </div>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-brand-white">
            Email
          </label>
          <input id="email" name="email" type="email" required className={fieldClass} placeholder="you@example.com" />
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="phone" className="mb-1.5 block text-sm font-medium text-brand-white">
            Phone <span className="font-normal text-brand-muted">(optional)</span>
          </label>
          <input id="phone" name="phone" className={fieldClass} placeholder="Your number" />
        </div>
        <div>
          <label htmlFor="service" className="mb-1.5 block text-sm font-medium text-brand-white">
            Service
          </label>
          <select id="service" name="service" className={fieldClass} defaultValue="">
            <option value="" disabled>
              Select a service
            </option>
            {services.map((s) => (
              <option key={s.slug} value={s.name}>
                {s.name}
              </option>
            ))}
            <option value="Not sure">Not sure / other</option>
          </select>
        </div>
      </div>

      <div>
        <label htmlFor="message" className="mb-1.5 block text-sm font-medium text-brand-white">
          What&apos;s going on?
        </label>
        <textarea
          id="message"
          name="message"
          required
          rows={5}
          className={fieldClass}
          placeholder="Tell us a bit about the problem or what you need help with"
        />
      </div>

      {status === 'error' && (
        <p className="text-sm text-brand-amber">
          {errorMessage || 'Something went wrong sending your message — please try again or email us directly.'}
        </p>
      )}

      <button type="submit" disabled={status === 'submitting'} className="btn-brand w-full sm:w-auto">
        {status === 'submitting' ? 'Sending…' : 'Send message'}
      </button>
    </form>
  )
}
