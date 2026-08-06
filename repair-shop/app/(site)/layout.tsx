import Navbar from '@/components/marketing/navbar'
import Footer from '@/components/marketing/footer'
import BackgroundFX from '@/components/marketing/background-fx'

export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="site-scope flex min-h-screen flex-col bg-brand-bg text-brand-white">
      <BackgroundFX />
      <Navbar />
      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  )
}
