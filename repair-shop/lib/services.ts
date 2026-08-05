export interface ServiceDetail {
  slug: string
  icon: 'computer' | 'printer' | 'support' | 'network' | 'wifi'
  name: string
  shortName: string
  tagline: string
  description: string
  highlights: string[]
  commonIssues: string[]
}

export const services: ServiceDetail[] = [
  {
    slug: 'computer-repair',
    icon: 'computer',
    name: 'Computer Repair',
    shortName: 'Computer Repair',
    tagline: 'Fast, careful diagnostics for laptops and desktops',
    description:
      'From a machine that won’t start to one that’s simply not what it used to be, our engineers diagnose the real fault first and only recommend the work that’s actually needed.',
    highlights: [
      'Free initial diagnostics on every job',
      'Genuine parts and certified components',
      'Data protected and backed up before any work begins',
      'Clear, upfront pricing before we start',
    ],
    commonIssues: [
      'Won’t turn on or keeps crashing',
      'Running slow or freezing',
      'Virus, malware or ransomware removal',
      'SSD, RAM and hardware upgrades',
      'Data recovery from failed drives',
      'Windows and macOS troubleshooting',
    ],
  },
  {
    slug: 'printer-repair',
    icon: 'printer',
    name: 'Printer Repair & Setup',
    shortName: 'Printers',
    tagline: 'Printers, scanners and multi-function devices sorted',
    description:
      'Printers rarely fail politely — they jam, drop off the network or refuse drivers at the worst possible moment. We get them reliable again and configured properly across every device in the house or office.',
    highlights: [
      'Support for all major printer brands',
      'Wireless and network printer configuration',
      'Shared printing set up across every device',
      'Maintenance plans for busy offices',
    ],
    commonIssues: [
      'Printer not detected or offline',
      'Driver and software conflicts',
      'Wireless printer won’t connect',
      'Paper jams and print quality issues',
      'Scanner and multi-function setup',
      'Print server and shared printer configuration',
    ],
  },
  {
    slug: 'it-support',
    icon: 'support',
    name: 'IT Support',
    shortName: 'IT Support',
    tagline: 'Dependable IT support for homes and small businesses',
    description:
      'On-demand or ongoing, remote or on-site — our IT support keeps your systems running so you can get on with your day. We work the same way an in-house IT team would, without the overhead.',
    highlights: [
      'Remote support for quick fixes, on-site for the rest',
      'Ongoing support plans for small businesses',
      'Microsoft 365 and Google Workspace setup',
      'Straightforward advice, no jargon',
    ],
    commonIssues: [
      'General troubleshooting and slow systems',
      'Software installation and licensing',
      'Cloud email and file storage setup',
      'New starter device setup',
      'Backups and system security',
      'One-off projects or rolling support contracts',
    ],
  },
  {
    slug: 'home-networks',
    icon: 'network',
    name: 'Home Network Installation',
    shortName: 'Home Networks',
    tagline: 'Reliable, whole-home networks done properly',
    description:
      'A good network is invisible — it just works, in every room, on every device. We design and install home and small office networks that are fast, secure and built to last.',
    highlights: [
      'Full network design for your property',
      'Structured ethernet cabling where it counts',
      'Secure router and firewall configuration',
      'Smart home and NAS device integration',
    ],
    commonIssues: [
      'New home network installation',
      'Ethernet cabling and network points',
      'Router setup and network security',
      'Multi-room and multi-floor coverage',
      'NAS and shared storage setup',
      'Smart home device integration',
    ],
  },
  {
    slug: 'wifi-troubleshooting',
    icon: 'wifi',
    name: 'WiFi Troubleshooting',
    shortName: 'WiFi Issues',
    tagline: 'No more dead zones, drop-outs or dodgy signal',
    description:
      'Slow WiFi is rarely about your broadband — it’s usually about coverage. We track down the cause and fix it properly, with mesh systems and extenders where they genuinely help.',
    highlights: [
      'On-site signal and interference testing',
      'Mesh WiFi design and installation',
      'Router placement and channel optimisation',
      'Guest network and device separation',
    ],
    commonIssues: [
      'Weak signal or dead zones',
      'Frequent drop-outs and reconnects',
      'Slow WiFi despite fast broadband',
      'Mesh system installation',
      'Too many devices, not enough bandwidth',
      'Guest and secure network setup',
    ],
  },
]

export function getServiceBySlug(slug: string) {
  return services.find((s) => s.slug === slug)
}
