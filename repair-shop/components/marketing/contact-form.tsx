'use client'

import { useState } from 'react'
import { services } from '@/lib/services'
import { CheckIcon } from './icons'

export default function ContactForm() {
  const [status, setStatus] = useState<'idle' | 'submitting' | 'sent' | 'error'>('idle')

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
    }

    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Failed to send')
      setStatus('sent')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <div className="rounded-2xl border border-brand-line bg-brand-mist p-8 text-center">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-gradient text-white">
          <CheckIcon size={22} />
        </span>
        <h3 className="mt-4 text-lg font-semibold text-brand-ink">Thanks — message sent</h3>
        <p className="mt-2 text-sm text-brand-slate">
          We'll get back to you as soon as we can, usually within one working day.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="mb-1.5 block text-sm font-medium text-brand-ink">
            Name
          </label>
          <input
            id="name"
            name="name"
            required
            className="w-full rounded-xl border border-brand-line px-4 py-3 text-sm text-brand-ink placeholder:text-brand-slate/70 focus:border-brand-teal focus:outline-none focus:ring-2 focus:ring-brand-teal/20"
            placeholder="Your name"
          />
        </div>
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-brand-ink">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="w-full rounded-xl border border-brand-line px-4 py-3 text-sm text-brand-ink placeholder:text-brand-slate/70 focus:border-brand-teal focus:outline-none focus:ring-2 focus:ring-brand-teal/20"
            placeholder="you@example.com"
          />
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <div>
          <label htmlFor="phone" className="mb-1.5 block text-sm font-medium text-brand-ink">
            Phone <span className="font-normal text-brand-slate">(optional)</span>
          </label>
          <input
            id="phone"
            name="phone"
            className="w-full rounded-xl border border-brand-line px-4 py-3 text-sm text-brand-ink placeholder:text-brand-slate/70 focus:border-brand-teal focus:outline-none focus:ring-2 focus:ring-brand-teal/20"
            placeholder="Your number"
          />
        </div>
        <div>
          <label htmlFor="service" className="mb-1.5 block text-sm font-medium text-brand-ink">
            Service
          </label>
          <select
            id="service"
            name="service"
            className="w-full rounded-xl border border-brand-line px-4 py-3 text-sm text-brand-ink focus:border-brand-teal focus:outline-none focus:ring-2 focus:ring-brand-teal/20"
            defaultValue=""
          >
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
        <label htmlFor="message" className="mb-1.5 block text-sm font-medium text-brand-ink">
          What's going on?
        </label>
        <textarea
          id="message"
          name="message"
          required
          rows={5}
          className="w-full rounded-xl border border-brand-line px-4 py-3 text-sm text-brand-ink placeholder:text-brand-slate/70 focus:border-brand-teal focus:outline-none focus:ring-2 focus:ring-brand-teal/20"
          placeholder="Tell us a bit about the problem or what you need help with"
        />
      </div>

      {status === 'error' && (
        <p className="text-sm text-red-600">
          Something went wrong sending your message — please try again or email us directly.
        </p>
      )}

      <button type="submit" disabled={status === 'submitting'} className="btn-brand w-full sm:w-auto">
        {status === 'submitting' ? 'Sending…' : 'Send message'}
      </button>
    </form>
  )
}
