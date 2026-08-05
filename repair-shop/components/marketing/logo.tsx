import Link from 'next/link'

interface LogoProps {
  dark?: boolean
  tagline?: boolean
  className?: string
}

export default function Logo({ dark = false, tagline = false, className }: LogoProps) {
  const inkClass = dark ? 'text-white' : 'text-brand-ink'
  const slateClass = dark ? 'text-slate-400' : 'text-brand-slate'

  return (
    <Link href="/" className={`inline-flex items-center gap-3 group ${className ?? ''}`}>
      <span className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-gradient shadow-sm">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="6" cy="6" r="2" fill="white" />
          <circle cx="18" cy="6" r="2" fill="white" />
          <circle cx="6" cy="18" r="2" fill="white" />
          <circle cx="18" cy="18" r="2" fill="white" />
          <circle cx="12" cy="12" r="2.6" fill="white" />
          <path d="M6 8v3a1 1 0 0 0 1 1h3M18 8v3a1 1 0 0 0-1 1h-3M6 16v-3a1 1 0 0 1 1-1h3M18 16v-3a1 1 0 0 1-1-1h-3"
            stroke="white" strokeWidth="1.4" strokeLinecap="round" opacity="0.9" />
        </svg>
      </span>
      <span className="flex flex-col leading-none">
        <span className="flex items-baseline gap-1">
          <span className={`text-lg font-bold tracking-tight ${inkClass}`}>404</span>
          <span className="text-lg font-bold tracking-tight brand-gradient-text">FIXED</span>
        </span>
        {tagline && (
          <span className={`mt-1 text-[10px] font-semibold uppercase tracking-[0.2em] ${slateClass}`}>
            Computer &amp; IT Specialists
          </span>
        )}
      </span>
    </Link>
  )
}
