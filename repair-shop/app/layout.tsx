import type { Metadata, Viewport } from 'next'
import { Space_Grotesk, Inter, JetBrains_Mono } from 'next/font/google'
import { SITE_URL } from '@/lib/site'
import './globals.css'

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? '404 Fixed'
const DESCRIPTION =
  '404 Fixed: fast, reliable IT support, network installs and WiFi troubleshooting for homes and businesses across Cardiff and Penarth. Check your postcode and book in minutes.'

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-display',
  display: 'swap',
})
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
})
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: `${APP_NAME} | IT Support, Network Installs & WiFi — Cardiff & Penarth`,
    template: `%s | ${APP_NAME}`,
  },
  description: DESCRIPTION,
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    siteName: APP_NAME,
    locale: 'en_GB',
    url: '/',
    title: `${APP_NAME} | IT Support, Network Installs & WiFi — Cardiff & Penarth`,
    description: DESCRIPTION,
  },
  twitter: {
    card: 'summary_large_image',
    title: `${APP_NAME} | IT Support, Network Installs & WiFi — Cardiff & Penarth`,
    description: DESCRIPTION,
  },
}

export const viewport: Viewport = {
  themeColor: '#05070C',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${spaceGrotesk.variable} ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased bg-brand-bg text-brand-white font-sans">
        {children}
      </body>
    </html>
  )
}
