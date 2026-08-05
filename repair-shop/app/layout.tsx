import type { Metadata, Viewport } from 'next'
import './globals.css'

const APP_NAME = process.env.NEXT_PUBLIC_APP_NAME ?? '404 Fixed'

export const metadata: Metadata = {
  title: {
    default: `${APP_NAME} — Computer Repair & IT Support`,
    template: `%s | ${APP_NAME}`,
  },
  description:
    'Trusted computer repair, printer support, home networking and IT support — for homes and businesses.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: APP_NAME,
  },
}

export const viewport: Viewport = {
  themeColor: '#0F172A',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased bg-white text-brand-ink">
        {children}
      </body>
    </html>
  )
}
