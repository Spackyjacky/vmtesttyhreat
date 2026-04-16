import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'
import JobStatusBadge from '@/components/job-status-badge'
import { formatTicketNumber, formatDateTime, formatCurrency } from '@/lib/utils'
import { JOB_STATUS_LABELS, type JobStatus } from '@/types'
import type { Job } from '@/types'

export const metadata = { title: 'Jobs' }

interface PageProps {
  searchParams: Promise<{ status?: string; q?: string }>
}

const STATUSES: JobStatus[] = ['intake', 'diagnosed', 'in_progress', 'waiting_parts', 'ready', 'collected']

export default async function JobsPage({ searchParams }: PageProps) {
  const { status, q } = await searchParams
  const supabase = await createClient()

  let query = supabase
    .from('jobs')
    .select('*, customer:customers(id,name,phone,email)')
    .order('created_at', { ascending: false })
    .limit(100)

  if (status && STATUSES.includes(status as JobStatus)) {
    query = query.eq('status', status)
  }

  if (q) {
    query = query.or(`device_make.ilike.%${q}%,device_model.ilike.%${q}%,reported_fault.ilike.%${q}%,imei.ilike.%${q}%`)
  }

  const { data: jobs } = await query

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-2xl font-bold text-fg">Jobs</h1>
        <Link href="/jobs/new" className="btn-primary flex items-center gap-2 text-sm">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14"/><path d="M12 5v14"/>
          </svg>
          New Ticket
        </Link>
      </div>

      {/* Search & filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <form className="flex-1">
          <input
            name="q"
            defaultValue={q}
            type="search"
            placeholder="Search by device, fault, IMEI…"
            className="input"
          />
        </form>
      </div>

      {/* Status tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 flex-wrap">
        <Link
          href="/jobs"
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${!status ? 'bg-primary text-white' : 'bg-surface-2 text-muted hover:text-fg'}`}
        >
          All
        </Link>
        {STATUSES.map((s) => (
          <Link
            key={s}
            href={`/jobs?status=${s}`}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${status === s ? 'bg-primary text-white' : 'bg-surface-2 text-muted hover:text-fg'}`}
          >
            {JOB_STATUS_LABELS[s]}
          </Link>
        ))}
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {!jobs?.length ? (
          <div className="text-center py-16 text-muted">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mx-auto mb-3 opacity-40">
              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
            </svg>
            <p>No jobs found.</p>
            {!status && !q && (
              <Link href="/jobs/new" className="text-primary hover:underline mt-2 inline-block">
                Create your first ticket →
              </Link>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  <th className="text-left text-muted font-medium py-3 px-4">Ticket</th>
                  <th className="text-left text-muted font-medium py-3 px-4">Customer</th>
                  <th className="text-left text-muted font-medium py-3 px-4 hidden md:table-cell">Device</th>
                  <th className="text-left text-muted font-medium py-3 px-4 hidden lg:table-cell">Fault</th>
                  <th className="text-left text-muted font-medium py-3 px-4">Status</th>
                  <th className="text-left text-muted font-medium py-3 px-4 hidden sm:table-cell">Technician</th>
                  <th className="text-right text-muted font-medium py-3 px-4 hidden md:table-cell">Price</th>
                  <th className="text-right text-muted font-medium py-3 px-4">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(jobs as unknown as Job[]).map((job) => (
                  <tr key={job.id} className="hover:bg-surface-2/50 transition-colors">
                    <td className="py-3 px-4">
                      <Link href={`/jobs/${job.id}`} className="font-mono text-primary hover:underline font-medium text-xs">
                        {formatTicketNumber(job.ticket_number)}
                      </Link>
                    </td>
                    <td className="py-3 px-4 text-fg">
                      {job.customer?.name ?? <span className="text-muted">Walk-in</span>}
                    </td>
                    <td className="py-3 px-4 text-muted hidden md:table-cell">
                      {job.device_make} {job.device_model}
                    </td>
                    <td className="py-3 px-4 text-muted hidden lg:table-cell max-w-[200px] truncate">
                      {job.reported_fault}
                    </td>
                    <td className="py-3 px-4">
                      <JobStatusBadge status={job.status} />
                    </td>
                    <td className="py-3 px-4 text-muted hidden sm:table-cell text-xs">
                      {job.technician_name ?? '—'}
                    </td>
                    <td className="py-3 px-4 text-right text-muted hidden md:table-cell">
                      {formatCurrency(job.final_price ?? job.quoted_price)}
                    </td>
                    <td className="py-3 px-4 text-right text-muted text-xs whitespace-nowrap">
                      {formatDateTime(job.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
