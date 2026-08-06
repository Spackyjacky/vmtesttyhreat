export interface ServiceDetail {
  slug: string
  icon: 'it-support' | 'network-installs' | 'wifi-help'
  name: string
  shortName: string
  tagline: string
  description: string
  highlights: string[]
  commonIssues: string[]
}

export const services: ServiceDetail[] = [
  {
    slug: 'it-support',
    icon: 'it-support',
    name: 'IT Support',
    shortName: 'IT Support',
    tagline: 'Remote and on-site help for the everyday stuff that grinds work to a halt',
    description:
      'Slow machines, account lockouts, printer chaos, software that won’t behave — we sort the everyday IT problems that eat into your day, remotely where we can and on-site where we can’t.',
    highlights: [
      'Remote support for quick fixes, on-site for the rest',
      'No guesswork — we diagnose the real fault first',
      'Straight answers, no jargon',
      'Business and home users welcome',
    ],
    commonIssues: [
      'Slow or freezing machines',
      'Account lockouts and login issues',
      'Printer chaos and driver conflicts',
      'Software that won’t behave',
      'New starter or new device setup',
      'General troubleshooting, on-demand or ongoing',
    ],
  },
  {
    slug: 'network-installs',
    icon: 'network-installs',
    name: 'Network Installs',
    shortName: 'Network Installs',
    tagline: 'Structured cabling, switches and secure setups built to last',
    description:
      'Structured cabling, switches and secure setups for home offices and small businesses. Built properly so it doesn’t need touching again for years.',
    highlights: [
      'Full network design for your property',
      'Structured cabling and network points',
      'Secure router and firewall configuration',
      'Built to last — no repeat call-outs',
    ],
    commonIssues: [
      'New home or office network installation',
      'Structured cabling and network points',
      'Switch and router configuration',
      'Secure network setup',
      'Multi-room and multi-floor coverage',
      'Small business network builds',
    ],
  },
  {
    slug: 'wifi-help',
    icon: 'wifi-help',
    name: 'WiFi Help',
    shortName: 'WiFi Help',
    tagline: 'Dead spots, drop-outs and painfully slow speeds — sorted',
    description:
      'Dead spots, drop-outs and painfully slow speeds — sorted. Mesh setups, signal mapping and honest advice on what your building actually needs.',
    highlights: [
      'On-site signal mapping',
      'Mesh WiFi design and installation',
      'Honest advice on what you actually need',
      'Router placement and channel optimisation',
    ],
    commonIssues: [
      'Dead zones and weak signal',
      'Frequent drop-outs',
      'Painfully slow speeds',
      'Mesh system installation',
      'Too many devices, not enough bandwidth',
      'Guest and secure network setup',
    ],
  },
]

export function getServiceBySlug(slug: string) {
  return services.find((s) => s.slug === slug)
}
