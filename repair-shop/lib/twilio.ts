import twilio from 'twilio'

const accountSid = process.env.TWILIO_ACCOUNT_SID
const authToken = process.env.TWILIO_AUTH_TOKEN
const fromNumber = process.env.TWILIO_PHONE_NUMBER

export async function sendSMS(to: string, message: string): Promise<boolean> {
  if (!accountSid || !authToken || !fromNumber) {
    console.warn('Twilio env vars not set — skipping SMS')
    return false
  }

  // Normalise UK numbers
  const normalised = to.replace(/^0/, '+44').replace(/\s/g, '')

  try {
    const client = twilio(accountSid, authToken)
    await client.messages.create({
      body: message,
      from: fromNumber,
      to: normalised,
    })
    return true
  } catch (err) {
    console.error('SMS send failed:', err)
    return false
  }
}
