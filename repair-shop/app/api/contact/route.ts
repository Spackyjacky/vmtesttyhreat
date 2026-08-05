import { NextResponse, type NextRequest } from 'next/server'
import { sendContactEnquiryEmail } from '@/lib/resend'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, email, phone, service, message } = body

    if (!name?.trim() || !email?.trim() || !message?.trim()) {
      return NextResponse.json({ error: 'Name, email and message are required' }, { status: 400 })
    }

    const sent = await sendContactEnquiryEmail({
      name: name.trim(),
      email: email.trim(),
      phone: phone?.trim() || undefined,
      service: service?.trim() || undefined,
      message: message.trim(),
    })

    if (!sent) {
      console.log('Contact enquiry received (email not sent):', { name, email, phone, service })
    }

    return NextResponse.json({ ok: true })
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 })
  }
}
