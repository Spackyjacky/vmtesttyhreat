import { Resend } from 'resend'

function getResendClient() {
  return new Resend(process.env.RESEND_API_KEY)
}

const FROM = `${process.env.RESEND_FROM_NAME ?? 'Repair Shop'} <${process.env.RESEND_FROM_EMAIL ?? 'noreply@example.com'}>`
const SHOP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? 'Repair Shop'
const SHOP_PHONE = process.env.NEXT_PUBLIC_SHOP_PHONE ?? ''
const SHOP_EMAIL = process.env.NEXT_PUBLIC_SHOP_EMAIL ?? process.env.RESEND_FROM_EMAIL ?? ''

export async function sendContactEnquiryEmail(enquiry: {
  name: string
  email: string
  phone?: string
  service?: string
  message: string
}): Promise<boolean> {
  if (!process.env.RESEND_API_KEY || !SHOP_EMAIL) {
    console.warn('Resend not configured — skipping contact enquiry email')
    return false
  }

  try {
    const html = `
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#F6F8FB;font-family:system-ui,sans-serif;color:#0F172A;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;border:1px solid #E4E9F1;">
        <tr>
          <td style="padding:28px 32px;background:#0B1220;">
            <h1 style="margin:0;font-size:18px;color:#ffffff;">New website enquiry</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 10px;"><strong>Name:</strong> ${enquiry.name}</p>
            <p style="margin:0 0 10px;"><strong>Email:</strong> ${enquiry.email}</p>
            ${enquiry.phone ? `<p style="margin:0 0 10px;"><strong>Phone:</strong> ${enquiry.phone}</p>` : ''}
            ${enquiry.service ? `<p style="margin:0 0 10px;"><strong>Service:</strong> ${enquiry.service}</p>` : ''}
            <p style="margin:16px 0 6px;"><strong>Message:</strong></p>
            <p style="margin:0;white-space:pre-wrap;line-height:1.6;">${enquiry.message}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`

    const { error } = await getResendClient().emails.send({
      from: FROM,
      to: SHOP_EMAIL,
      reply_to: enquiry.email,
      subject: `${SHOP_NAME} — New enquiry from ${enquiry.name}`,
      html,
    })

    if (error) {
      console.error('Resend error:', error)
      return false
    }
    return true
  } catch (err) {
    console.error('Contact enquiry email failed:', err)
    return false
  }
}

export async function sendStatusEmail(
  to: string,
  customerName: string,
  ticketNumber: string,
  statusMessage: string,
  deviceLabel: string
): Promise<boolean> {
  if (!process.env.RESEND_API_KEY) {
    console.warn('Resend API key not set — skipping email')
    return false
  }

  try {
    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Repair Update</title>
</head>
<body style="margin:0;padding:0;background:#09090b;font-family:system-ui,sans-serif;color:#fafafa;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#09090b;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

          <!-- Header -->
          <tr>
            <td style="background:#18181b;border-radius:12px 12px 0 0;padding:32px 40px;border-bottom:2px solid #dc2626;">
              <h1 style="margin:0;font-size:24px;font-weight:700;color:#fafafa;">
                <span style="color:#dc2626;">&#9679;</span> ${SHOP_NAME}
              </h1>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="background:#18181b;padding:40px;">
              <p style="margin:0 0 16px;font-size:16px;color:#a1a1aa;">Hi ${customerName},</p>
              <p style="margin:0 0 24px;font-size:18px;color:#fafafa;line-height:1.6;">
                ${statusMessage}
              </p>
              <table width="100%" cellpadding="0" cellspacing="0" style="background:#27272a;border-radius:8px;padding:20px;margin-bottom:24px;">
                <tr>
                  <td style="padding:8px 0;">
                    <span style="color:#a1a1aa;font-size:14px;">Ticket</span>
                    <span style="float:right;color:#fafafa;font-weight:600;font-family:monospace;">${ticketNumber}</span>
                  </td>
                </tr>
                <tr>
                  <td style="padding:8px 0;border-top:1px solid #3f3f46;">
                    <span style="color:#a1a1aa;font-size:14px;">Device</span>
                    <span style="float:right;color:#fafafa;">${deviceLabel}</span>
                  </td>
                </tr>
              </table>
              ${SHOP_PHONE ? `<p style="margin:0;color:#a1a1aa;font-size:14px;">Questions? Call us on <a href="tel:${SHOP_PHONE}" style="color:#dc2626;">${SHOP_PHONE}</a></p>` : ''}
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#27272a;border-radius:0 0 12px 12px;padding:20px 40px;text-align:center;">
              <p style="margin:0;color:#71717a;font-size:13px;">&copy; ${new Date().getFullYear()} ${SHOP_NAME}. All rights reserved.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>`

    const { error } = await getResendClient().emails.send({
      from: FROM,
      to,
      subject: `${SHOP_NAME} — Repair Update for ${ticketNumber}`,
      html,
    })

    if (error) {
      console.error('Resend error:', error)
      return false
    }
    return true
  } catch (err) {
    console.error('Email send failed:', err)
    return false
  }
}
