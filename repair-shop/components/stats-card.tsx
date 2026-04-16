import { cn } from '@/lib/utils'

interface StatsCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  accent?: 'red' | 'green' | 'yellow' | 'blue'
  sub?: string
}

const ACCENT_CLASSES = {
  red: 'bg-red-900/20 text-primary border-red-900/40',
  green: 'bg-green-900/20 text-green-400 border-green-900/40',
  yellow: 'bg-yellow-900/20 text-yellow-400 border-yellow-900/40',
  blue: 'bg-blue-900/20 text-blue-400 border-blue-900/40',
}

const ICON_CLASSES = {
  red: 'bg-primary-muted text-primary',
  green: 'bg-green-900/40 text-green-400',
  yellow: 'bg-yellow-900/40 text-yellow-400',
  blue: 'bg-blue-900/40 text-blue-400',
}

export default function StatsCard({ label, value, icon, accent = 'red', sub }: StatsCardProps) {
  return (
    <div className={cn('card border', ACCENT_CLASSES[accent])}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-muted uppercase tracking-wider mb-1">{label}</p>
          <p className="text-3xl font-bold text-fg">{value}</p>
          {sub && <p className="text-xs text-muted mt-1">{sub}</p>}
        </div>
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', ICON_CLASSES[accent])}>
          {icon}
        </div>
      </div>
    </div>
  )
}
