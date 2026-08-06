import { NextResponse, type NextRequest } from 'next/server'
import { z } from 'zod'
import { sendContactEnquiryEmail } from '@/lib/resend'

const contactSchema = z.object({
  name: z.string().trim().min(1, 'Name is required').max(100),
  email: z.string().trim().email('Enter a valid email address').max(200),
  phone: z.string().trim().max(30).optional(),
  service: z.string().trim().max(100).optional(),
  message: z.string().trim().min(1, 'Message is required').max(3000),
  // Honeypot — real users never see or fill this field. If it's non-empty, treat as spam.
  company: z.string().optional(),
})

export async function POST(request: NextRequest) {
  let body: unknown
  try {
    body = await request.json()
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid request body' }, { status: 400 })
  }

  const parsed = contactSchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json(
      { ok: false, error: parsed.error.issues[0]?.message ?? 'Invalid submission' },
      { status: 400 }
    )
  }

  const { company, ...enquiry } = parsed.data
  if (company) {
    // Honeypot tripped — pretend success so bots don't learn to avoid this field.
    return NextResponse.json({ ok: true })
  }

  const sent = await sendContactEnquiryEmail({
    name: enquiry.name,
    email: enquiry.email,
    phone: enquiry.phone || undefined,
    service: enquiry.service || undefined,
    message: enquiry.message,
  })

  if (!sent) {
    return NextResponse.json(
      { ok: false, error: 'Message could not be delivered — please email us directly.' },
      { status: 502 }
    )
  }

  return NextResponse.json({ ok: true })
}
