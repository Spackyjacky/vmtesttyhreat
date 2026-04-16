'use client'

import { useEffect, useState, use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import toast, { Toaster } from 'react-hot-toast'
import JobStatusBadge from '@/components/job-status-badge'
import { formatTicketNumber, formatDateTime, formatCurrency, generateCollectionLink } from '@/lib/utils'
import {
  JOB_STATUS_LABELS, DEVICE_TYPE_LABELS,
  type Job, type JobStatus, type InventoryItem, type JobPart
} from '@/types'

const STATUS_FLOW: JobStatus[] = ['intake', 'diagnosed', 'in_progress', 'waiting_parts', 'ready', 'collected']

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const router = useRouter()
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [internalNote, setInternalNote] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [finalPrice, setFinalPrice] = useState('')
  const [savingPrice, setSavingPrice] = useState(false)
  const [technicianName, setTechnicianName] = useState('')
  const [inventory, setInventory] = useState<InventoryItem[]>([])
  const [selectedPart, setSelectedPart] = useState('')
  const [partQty, setPartQty] = useState('1')
  const [addingPart, setAddingPart] = useState(false)
  const [parts, setParts] = useState<JobPart[]>([])

  useEffect(() => {
    loadJob()
    loadInventory()
  }, [id])

  async function loadJob() {
    const res = await fetch(`/api/jobs/${id}`)
    if (!res.ok) { router.push('/jobs'); return }
    const data = await res.json()
    setJob(data.job)
    setFinalPrice(data.job.final_price?.toString() ?? '')
    setTechnicianName(data.job.technician_name ?? '')
    setInternalNote(data.job.internal_notes ?? '')
    setParts(data.job.parts ?? [])
    setLoading(false)
  }

  async function loadInventory() {
    const res = await fetch('/api/inventory')
    const data = await res.json()
    setInventory(data.items ?? [])
  }

  async function updateStatus(newStatus: JobStatus) {
    setUpdatingStatus(true)
    const res = await fetch(`/api/jobs/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    })
    const data = await res.json()
    if (!res.ok) { toast.error(data.error ?? 'Failed to update status'); setUpdatingStatus(false); return }
    setJob(data.job)
    toast.success(`Status updated to ${JOB_STATUS_LABELS[newStatus]}`)
    if (data.notified) toast.success('Customer notified via SMS/email')
    setUpdatingStatus(false)
  }

  async function saveInternalNote() {
    setSavingNote(true)
    const res = await fetch(`/api/jobs/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ internal_notes: internalNote, final_price: finalPrice ? parseFloat(finalPrice) : null, technician_name: technicianName }),
    })
    const data = await res.json()
    if (!res.ok) toast.error('Failed to save')
    else { setJob(data.job); toast.success('Saved') }
    setSavingNote(false)
  }

  async function addPart() {
    if (!selectedPart) return
    setAddingPart(true)
    const item = inventory.find((i) => i.id === selectedPart)
    const res = await fetch(`/api/jobs/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        add_part: {
          inventory_id: item?.id,
          part_name: item?.part_name ?? 'Unknown part',
          quantity: parseInt(partQty, 10) || 1,
          unit_price: item?.sell_price,
        },
      }),
    })
    const data = await res.json()
    if (!res.ok) toast.error(data.error ?? 'Failed to add part')
    else { setParts(data.parts ?? []); toast.success('Part added'); setSelectedPart(''); setPartQty('1') }
    setAddingPart(false)
  }

  function copyCollectionLink() {
    const link = generateCollectionLink(id)
    navigator.clipboard.writeText(link)
    toast.success('Collection link copied!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!job) return null

  const currentStatusIndex = STATUS_FLOW.indexOf(job.status)

  return (
    <>
      <Toaster position="top-center" toastOptions={{ style: { background: '#18181b', color: '#fafafa', border: '1px solid #3f3f46' } }} />

      <div className="space-y-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-start gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <button onClick={() => router.back()} className="text-muted hover:text-fg transition-colors">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m15 18-6-6 6-6"/>
              </svg>
            </button>
            <div>
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl font-bold text-fg font-mono">{formatTicketNumber(job.ticket_number)}</h1>
                <JobStatusBadge status={job.status} />
              </div>
              <p className="text-muted text-sm mt-0.5">{job.device_make} {job.device_model} · {job.customer?.name ?? 'Walk-in'}</p>
            </div>
          </div>
          <div className="ml-auto flex gap-2 flex-wrap">
            {job.status === 'ready' && (
              <button onClick={copyCollectionLink} className="btn-secondary text-sm flex items-center gap-2">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                </svg>
                Copy collection link
              </button>
            )}
          </div>
        </div>

        {/* Status pipeline */}
        <div className="card">
          <h2 className="font-semibold text-fg mb-4 text-sm">Update Status</h2>
          <div className="flex gap-1 overflow-x-auto pb-1">
            {STATUS_FLOW.map((s, i) => {
              const isPast = i < currentStatusIndex
              const isCurrent = i === currentStatusIndex
              const isNext = i === currentStatusIndex + 1
              return (
                <button
                  key={s}
                  disabled={updatingStatus || isCurrent || isPast}
                  onClick={() => isNext && updateStatus(s)}
                  className={`flex-1 min-w-[90px] px-2 py-2 rounded-lg text-xs font-medium border transition-all ${
                    isCurrent
                      ? 'border-primary bg-primary-muted text-primary'
                      : isPast
                      ? 'border-border bg-surface-2 text-muted opacity-50'
                      : isNext
                      ? 'border-border bg-surface-2 text-fg hover:border-primary hover:bg-primary-muted cursor-pointer'
                      : 'border-border bg-surface-2 text-muted opacity-30 cursor-not-allowed'
                  }`}
                >
                  {isPast && '✓ '}
                  {JOB_STATUS_LABELS[s]}
                </button>
              )
            })}
          </div>
          {updatingStatus && <p className="text-xs text-muted mt-2 text-center">Updating and sending notifications…</p>}
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Device Info */}
          <div className="card space-y-3">
            <h2 className="font-semibold text-fg">Device</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">Type</dt>
                <dd className="text-fg">{DEVICE_TYPE_LABELS[job.device_type]}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Make</dt>
                <dd className="text-fg">{job.device_make}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">Model</dt>
                <dd className="text-fg">{job.device_model}</dd>
              </div>
              {job.imei && (
                <div className="flex justify-between">
                  <dt className="text-muted">IMEI</dt>
                  <dd className="text-fg font-mono text-xs">{job.imei}</dd>
                </div>
              )}
              {job.password && (
                <div className="flex justify-between">
                  <dt className="text-muted">Password</dt>
                  <dd className="text-fg font-mono">{job.password}</dd>
                </div>
              )}
              <div className="flex justify-between">
                <dt className="text-muted">Backup advised</dt>
                <dd className={job.backup_required ? 'text-success' : 'text-muted'}>
                  {job.backup_required ? 'Yes' : 'No'}
                </dd>
              </div>
            </dl>
            <div className="pt-2 border-t border-border">
              <p className="text-xs text-muted font-medium mb-1">Reported fault</p>
              <p className="text-sm text-fg">{job.reported_fault}</p>
            </div>
            {job.notes && (
              <div className="pt-2 border-t border-border">
                <p className="text-xs text-muted font-medium mb-1">Customer notes</p>
                <p className="text-sm text-fg">{job.notes}</p>
              </div>
            )}
          </div>

          {/* Customer Info */}
          <div className="card space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-fg">Customer</h2>
              {job.customer && (
                <Link href={`/customers/${job.customer_id}`} className="text-xs text-primary hover:underline">View profile →</Link>
              )}
            </div>
            {job.customer ? (
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-muted">Name</dt>
                  <dd className="text-fg font-medium">{job.customer.name}</dd>
                </div>
                {job.customer.phone && (
                  <div className="flex justify-between">
                    <dt className="text-muted">Phone</dt>
                    <dd><a href={`tel:${job.customer.phone}`} className="text-primary hover:underline">{job.customer.phone}</a></dd>
                  </div>
                )}
                {job.customer.email && (
                  <div className="flex justify-between">
                    <dt className="text-muted">Email</dt>
                    <dd><a href={`mailto:${job.customer.email}`} className="text-primary hover:underline text-xs">{job.customer.email}</a></dd>
                  </div>
                )}
              </dl>
            ) : (
              <p className="text-muted text-sm">Walk-in customer</p>
            )}

            <div className="pt-2 border-t border-border space-y-3">
              <h3 className="font-medium text-fg text-sm">Financials</h3>
              <div className="flex justify-between text-sm">
                <span className="text-muted">Quoted price</span>
                <span className="text-fg">{formatCurrency(job.quoted_price)}</span>
              </div>
              <div>
                <label className="label text-xs">Final price (£)</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    className="input"
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    value={finalPrice}
                    onChange={(e) => setFinalPrice(e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="label text-xs">Technician</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Name"
                  value={technicianName}
                  onChange={(e) => setTechnicianName(e.target.value)}
                />
              </div>
              <div>
                <label className="label text-xs">Internal notes</label>
                <textarea
                  className="input resize-none text-sm"
                  rows={3}
                  placeholder="Internal notes (not shown to customer)…"
                  value={internalNote}
                  onChange={(e) => setInternalNote(e.target.value)}
                />
              </div>
              <button onClick={saveInternalNote} disabled={savingNote} className="btn-primary w-full text-sm">
                {savingNote ? 'Saving…' : 'Save changes'}
              </button>
            </div>

            <div className="pt-2 border-t border-border text-xs text-muted space-y-1">
              <div className="flex justify-between">
                <span>Created</span>
                <span>{formatDateTime(job.created_at)}</span>
              </div>
              {job.collected_at && (
                <div className="flex justify-between">
                  <span>Collected</span>
                  <span>{formatDateTime(job.collected_at)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Parts used */}
          <div className="card space-y-3">
            <h2 className="font-semibold text-fg">Parts Used</h2>
            {parts.length === 0 ? (
              <p className="text-muted text-sm">No parts logged yet.</p>
            ) : (
              <div className="space-y-2">
                {parts.map((p) => (
                  <div key={p.id} className="flex justify-between text-sm border-b border-border pb-2 last:border-0">
                    <span className="text-fg">{p.part_name} ×{p.quantity}</span>
                    <span className="text-muted">{formatCurrency(p.unit_price ? p.unit_price * p.quantity : null)}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2 pt-2">
              <select
                className="input text-sm flex-1"
                value={selectedPart}
                onChange={(e) => setSelectedPart(e.target.value)}
              >
                <option value="">Select part from inventory…</option>
                {inventory.map((i) => (
                  <option key={i.id} value={i.id} disabled={i.quantity === 0}>
                    {i.part_name} {i.quantity === 0 ? '(out of stock)' : `(${i.quantity} in stock)`}
                  </option>
                ))}
              </select>
              <input
                type="number"
                className="input w-16 text-sm text-center"
                value={partQty}
                min="1"
                onChange={(e) => setPartQty(e.target.value)}
              />
              <button onClick={addPart} disabled={addingPart || !selectedPart} className="btn-primary text-sm px-3">
                Add
              </button>
            </div>
          </div>

          {/* Photos */}
          <div className="card space-y-3">
            <h2 className="font-semibold text-fg">Photos</h2>
            {!job.photos?.length ? (
              <p className="text-muted text-sm">No photos attached.</p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {job.photos.map((p) => (
                  <div key={p.id} className="relative rounded-lg overflow-hidden">
                    <div className="relative h-32 bg-surface-2">
                      <Image src={p.url} alt={p.photo_type} fill className="object-cover" />
                    </div>
                    <p className="text-xs text-muted mt-1 capitalize">{p.photo_type.replace('_', ' ')}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Signature */}
            {job.signature && (
              <div className="pt-3 border-t border-border">
                <h3 className="text-sm font-medium text-fg mb-2">Collection Signature</h3>
                <div className="relative h-24 bg-white rounded-lg overflow-hidden">
                  <Image src={job.signature.signature_url} alt="Signature" fill className="object-contain p-2" />
                </div>
                <p className="text-xs text-muted mt-1">
                  Collected by {job.signature.customer_name ?? 'unknown'} · {formatDateTime(job.signature.created_at)}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
