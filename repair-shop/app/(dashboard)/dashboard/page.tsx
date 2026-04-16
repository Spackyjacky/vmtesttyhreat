import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import StatsCard from '@/components/stats-card'
import JobStatusBadge from '@/components/job-status-badge'
import { formatTicketNumber, formatRelative, formatCurrency } from '@/lib/utils'
import type { Job } from '@/types'

export const metadata = { title: 'Dashboard' }

export default async function DashboardPage() {
  const supabase = await createClient()

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const [
    { count: openCount },
    { count: readyCount },
    { count: todayCount },
    { count: lowStockCount },
    { data: recentJobs },
  ] = await Promise.all([
    supabase
      .from('jobs')
      .select('*', { count: 'exact', head: true })
      .not('status', 'in', '(collected)'),
    supabase
      .from('jobs')
      .select('*', { count: 'exact', head: true })
      .eq('status', 'ready'),
    supabase
      .from('jobs')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', today.toISOString()),
    supabase
      .from('inventory')
      .select('*', { count: 'exact', head: true })
      .filter('quantity', 'lte', 'reorder_threshold'),
    supabase
      .from('jobs')
      .select('*, customer:customers(id,name,phone,email)')
      .order('created_at', { ascending: false })
      .limit(10),
  ])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-fg">Dashboard</h1>
          <p className="text-muted text-sm mt-0.5">
            {new Date().toLocaleDateString('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Link href="/jobs/new" className="btn-primary flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14"/><path d="M12 5v14"/>
          </svg>
          New Ticket
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          label="Open Jobs"
          value={openCount ?? 0}
          accent="red"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
          }
        />
        <StatsCard
          label="Ready to Collect"
          value={readyCount ?? 0}
          accent="green"
          sub="Awaiting customer"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 6 9 17l-5-5"/>
            </svg>
          }
        />
        <StatsCard
          label="Jobs Today"
          value={todayCount ?? 0}
          accent="blue"
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>
            </svg>
          }
        />
        <StatsCard
          label="Low Stock Alerts"
          value={lowStockCount ?? 0}
          accent={lowStockCount ? 'yellow' : 'green'}
          sub={lowStockCount ? 'Parts need reordering' : 'Stock levels OK'}
          icon={
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/>
            </svg>
          }
        />
      </div>

      {/* Recent Jobs */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-fg">Recent Jobs</h2>
          <Link href="/jobs" className="text-sm text-primary hover:underline">View all</Link>
        </div>

        {!recentJobs?.length ? (
          <div className="text-center py-12 text-muted">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 opacity-40">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            <p>No jobs yet. <Link href="/jobs/new" className="text-primary hover:underline">Create your first ticket.</Link></p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left text-muted font-medium pb-3 pr-4">Ticket</th>
                  <th className="text-left text-muted font-medium pb-3 pr-4">Customer</th>
                  <th className="text-left text-muted font-medium pb-3 pr-4 hidden sm:table-cell">Device</th>
                  <th className="text-left text-muted font-medium pb-3 pr-4">Status</th>
                  <th className="text-left text-muted font-medium pb-3 hidden md:table-cell">Created</th>
                  <th className="text-right text-muted font-medium pb-3">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(recentJobs as unknown as Job[]).map((job) => (
                  <tr key={job.id} className="hover:bg-surface-2 transition-colors">
                    <td className="py-3 pr-4">
                      <Link href={`/jobs/${job.id}`} className="font-mono text-primary hover:underline font-medium">
                        {formatTicketNumber(job.ticket_number)}
                      </Link>
                    </td>
                    <td className="py-3 pr-4">
                      <span className="text-fg">{job.customer?.name ?? 'Walk-in'}</span>
                    </td>
                    <td className="py-3 pr-4 hidden sm:table-cell text-muted">
                      {job.device_make} {job.device_model}
                    </td>
                    <td className="py-3 pr-4">
                      <JobStatusBadge status={job.status} />
                    </td>
                    <td className="py-3 hidden md:table-cell text-muted">
                      {formatRelative(job.created_at)}
                    </td>
                    <td className="py-3 text-right text-muted">
                      {formatCurrency(job.final_price ?? job.quoted_price)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Status pipeline */}
      <div className="card">
        <h2 className="font-semibold text-fg mb-4">Repair Pipeline</h2>
        <div className="flex gap-1 overflow-x-auto pb-2">
          {(['intake','diagnosed','in_progress','waiting_parts','ready','collected'] as const).map((status) => (
            <Link
              key={status}
              href={`/jobs?status=${status}`}
              className="flex-1 min-w-[100px] bg-surface-2 hover:bg-border rounded-lg p-3 text-center transition-colors"
            >
              <JobStatusBadge status={status} className="mb-2" />
              <p className="text-xs text-muted">View all</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
