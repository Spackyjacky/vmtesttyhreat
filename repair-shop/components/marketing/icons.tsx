interface IconProps {
  className?: string
  size?: number
}

const base = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function ComputerIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <rect x="3" y="4" width="18" height="12" rx="1.5" />
      <path d="M8 20h8M12 16v4" />
    </svg>
  )
}

export function PrinterIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M6 9V4h12v5" />
      <rect x="4" y="9" width="16" height="8" rx="1.5" />
      <path d="M8 14h8v6H8z" />
    </svg>
  )
}

export function SupportIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M4 13a8 8 0 0 1 16 0" />
      <rect x="2.5" y="13" width="4" height="6" rx="1.2" />
      <rect x="17.5" y="13" width="4" height="6" rx="1.2" />
      <path d="M19.5 19v.5A3.5 3.5 0 0 1 16 23h-2.5" />
    </svg>
  )
}

export function NetworkIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <rect x="9" y="2.5" width="6" height="4" rx="1" />
      <rect x="2.5" y="17.5" width="6" height="4" rx="1" />
      <rect x="15.5" y="17.5" width="6" height="4" rx="1" />
      <path d="M12 6.5v5M12 11.5H5.5v6M12 11.5h6.5v6" />
    </svg>
  )
}

export function WifiIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M2.5 8.5a14.5 14.5 0 0 1 19 0" />
      <path d="M5.8 12.3a10 10 0 0 1 12.4 0" />
      <path d="M9 16a5 5 0 0 1 6 0" />
      <circle cx="12" cy="19.5" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  )
}

export const SERVICE_ICONS = {
  computer: ComputerIcon,
  printer: PrinterIcon,
  support: SupportIcon,
  network: NetworkIcon,
  wifi: WifiIcon,
}

export function CheckIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M8 12.2l2.6 2.6L16.2 9" />
    </svg>
  )
}

export function ArrowRightIcon({ className, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M4 12h16M13 5l7 7-7 7" />
    </svg>
  )
}

export function MenuIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </svg>
  )
}

export function CloseIcon({ className, size = 24 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  )
}

export function ChevronDownIcon({ className, size = 16 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

export function MapPinIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M12 21s7-6.5 7-12a7 7 0 1 0-14 0c0 5.5 7 12 7 12z" />
      <circle cx="12" cy="9" r="2.4" />
    </svg>
  )
}

export function PhoneIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M4.5 3.5h3.2l1.5 4.3-2.1 1.6a12 12 0 0 0 5.5 5.5l1.6-2.1 4.3 1.5v3.2a1.5 1.5 0 0 1-1.6 1.5A16.5 16.5 0 0 1 3 4.6a1.5 1.5 0 0 1 1.5-1.1z" />
    </svg>
  )
}

export function MailIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <rect x="3" y="5" width="18" height="14" rx="1.8" />
      <path d="M3.5 6.5l8.5 6 8.5-6" />
    </svg>
  )
}

export function ClockIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <circle cx="12" cy="12" r="9.5" />
      <path d="M12 7v5.5l3.8 2.2" />
    </svg>
  )
}

export function ShieldIcon({ className, size = 20 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" {...base} className={className}>
      <path d="M12 2.5l7.5 3v6c0 5-3.2 8.5-7.5 10-4.3-1.5-7.5-5-7.5-10v-6z" />
      <path d="M8.7 12.2l2.3 2.3 4.3-4.6" />
    </svg>
  )
}

export function StarIcon({ className, size = 18 }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" stroke="none" className={className}>
      <path d="M12 2.8l2.7 5.9 6.4.7-4.8 4.4 1.3 6.4L12 16.9l-5.6 3.3 1.3-6.4-4.8-4.4 6.4-.7L12 2.8z" />
    </svg>
  )
}
