export const SITE_URL = process.env.NEXT_PUBLIC_APP_URL ?? 'https://404fixed.co.uk'
export const SUMUP_BOOKING_URL = 'https://www.sumupbookings.com/404-fixed'
export const CONTACT_EMAIL = process.env.NEXT_PUBLIC_SHOP_EMAIL ?? 'hello@404fixed.co.uk'
export const SERVICE_AREA = 'Cardiff & Penarth'

export interface CoverageDistrict {
  code: string
  name: string
}

export const COVERED_DISTRICTS: CoverageDistrict[] = [
  { code: 'CF3', name: 'St Mellons & Rumney' },
  { code: 'CF5', name: 'Canton & Ely' },
  { code: 'CF10', name: 'City Centre' },
  { code: 'CF11', name: 'Riverside & Bay' },
  { code: 'CF14', name: 'Heath & Whitchurch' },
  { code: 'CF15', name: 'Radyr & Tongwynlais' },
  { code: 'CF23', name: 'Cyncoed & Pentwyn' },
  { code: 'CF24', name: 'Roath & Adamsdown' },
  { code: 'CF64', name: 'Penarth' },
]

export const COVERED_CODES = COVERED_DISTRICTS.map((d) => d.code)
