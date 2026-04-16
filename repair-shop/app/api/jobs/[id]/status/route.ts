import { NextResponse, type NextRequest } from 'next/server'
import { createAdminClient } from '@/lib/supabase/server'
import { sendSMS } from '@/lib/twilio'
import { sendStatusEmail } from '@/lib/resend'
import { STATUS_NOTIFICATION_MESSAGES, type JobStatus } from '@/types'
import { formatTicketNumber } from '@/lib/utils'

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = createAdminClient()

  try {
    const body = await request.json()
    const { status, signature_url, collector_name } = body

    const validStatuses: JobStatus[] = ['intake', 'diagnosed', 'in_progress', 'waiting_parts', 'ready', 'collected']
    if (!validStatuses.includes(status)) {
      return NextResponse.json({ error: 'Invalid status' }, { status: 400 })
    }

    const updates: Record<string, unknown> = { status }
    if (status === 'collected') {
      updates.collected_at = new Date().toISOString()
    }

    // Update job status
    const { data: job, error: updateError } = await supabase
      .from('jobs')
      .update(updates)
      .eq('id', id)
      .select('*, customer:customers(id,name,phone,email), photos:job_photos(*), signature:signatures(*), parts:job_parts(*)')
      .single()

    if (updateError || !job) {
      return NextResponse.json({ error: updateError?.message ?? 'Job not found' }, { status: 500 })
    }

    // Save signature if provided (collection step)
    if (signature_url && status === 'collected') {
      await supabase.from('signatures').upsert({
        job_id: id,
        signature_url,
        collected_by: collector_name ?? 'Customer',
        customer_name: collector_name ?? job.customer?.name ?? null,
      })
    }

    // Send notifications
    let notified = false
    const message = STATUS_NOTIFICATION_MESSAGES[status as JobStatus]
    const customer = job.customer

    if (message && customer) {
      const shopName = process.env.NEXT_PUBLIC_APP_NAME ?? 'Repair Shop'
      const ticketRef = formatTicketNumber(job.ticket_number)
      const deviceLabel = `${job.device_make} ${job.device_model}`
      const fullMessage = `${shopName}: ${message} (Ticket ${ticketRef})`

      const notifPromises: Promise<boolean>[] = []

      if (customer.phone) {
        notifPromises.push(sendSMS(customer.phone, fullMessage))
      }
      if (customer.email) {
        notifPromises.push(
          sendStatusEmail(customer.email, customer.name, ticketRef, message, deviceLabel)
        )
      }

      const results = await Promise.all(notifPromises)
      notified = results.some(Boolean)

      // Log notifications
      const logs = []
      if (customer.phone) {
        logs.push({ job_id: id, type: 'sms', recipient: customer.phone, message: fullMessage, status: results[0] ? 'sent' : 'failed' })
      }
      if (customer.email) {
        logs.push({ job_id: id, type: 'email', recipient: customer.email, message, status: results[results.length - 1] ? 'sent' : 'failed' })
      }
      if (logs.length) {
        await supabase.from('notification_log').insert(logs)
      }
    }

    return NextResponse.json({ job, notified })
  } catch (e) {
    console.error(e)
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 })
  }
}
