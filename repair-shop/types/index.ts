export type JobStatus =
  | 'intake'
  | 'diagnosed'
  | 'in_progress'
  | 'waiting_parts'
  | 'ready'
  | 'collected'

export type DeviceType = 'phone' | 'tablet' | 'computer' | 'console' | 'other'

export type PhotoType = 'intake' | 'damage' | 'repair' | 'completion'

export type NotificationType = 'sms' | 'email'

export interface Customer {
  id: string
  name: string
  phone: string | null
  email: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Job {
  id: string
  ticket_number: number
  customer_id: string | null
  customer?: Customer | null
  device_type: DeviceType
  device_make: string
  device_model: string
  imei: string | null
  reported_fault: string
  password: string | null
  backup_required: boolean
  backup_completed: boolean
  status: JobStatus
  technician_name: string | null
  quoted_price: number | null
  final_price: number | null
  notes: string | null
  internal_notes: string | null
  created_at: string
  updated_at: string
  collected_at: string | null
  photos?: JobPhoto[]
  signature?: Signature | null
  parts?: JobPart[]
}

export interface JobPhoto {
  id: string
  job_id: string
  url: string
  photo_type: PhotoType
  caption: string | null
  created_at: string
}

export interface Signature {
  id: string
  job_id: string
  signature_url: string
  collected_by: string | null
  customer_name: string | null
  created_at: string
}

export interface InventoryItem {
  id: string
  part_name: string
  sku: string | null
  description: string | null
  quantity: number
  reorder_threshold: number
  cost_price: number | null
  sell_price: number | null
  supplier: string | null
  created_at: string
  updated_at: string
}

export interface JobPart {
  id: string
  job_id: string
  inventory_id: string | null
  part_name: string
  quantity: number
  unit_price: number | null
  created_at: string
  inventory?: InventoryItem | null
}

export interface NotificationLog {
  id: string
  job_id: string
  type: NotificationType
  recipient: string
  message: string | null
  status: string
  sent_at: string
}

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  intake: 'Intake',
  diagnosed: 'Diagnosed',
  in_progress: 'In Progress',
  waiting_parts: 'Waiting Parts',
  ready: 'Ready',
  collected: 'Collected',
}

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  intake: 'bg-blue-900/40 text-blue-300 border-blue-700',
  diagnosed: 'bg-purple-900/40 text-purple-300 border-purple-700',
  in_progress: 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  waiting_parts: 'bg-orange-900/40 text-orange-300 border-orange-700',
  ready: 'bg-green-900/40 text-green-300 border-green-700',
  collected: 'bg-zinc-800 text-zinc-400 border-zinc-600',
}

export const DEVICE_TYPE_LABELS: Record<DeviceType, string> = {
  phone: 'Phone',
  tablet: 'Tablet',
  computer: 'Computer / Laptop',
  console: 'Games Console',
  other: 'Other',
}

export const STATUS_NOTIFICATION_MESSAGES: Partial<Record<JobStatus, string>> = {
  diagnosed: 'Your device has been assessed. We will be in touch shortly with a quote.',
  in_progress: 'Great news — we have started working on your device.',
  waiting_parts: 'We are waiting for parts to arrive. We will update you as soon as they are in.',
  ready: 'Your device is ready for collection! Please bring this message as reference.',
  collected: 'Thank you for choosing us. We hope to see you again!',
}
