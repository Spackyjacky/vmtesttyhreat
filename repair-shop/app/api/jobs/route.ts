import { NextResponse, type NextRequest } from 'next/server'
import { createAdminClient } from '@/lib/supabase/server'

export async function GET(request: NextRequest) {
  const supabase = createAdminClient()
  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status')
  const q = searchParams.get('q')
  const limit = parseInt(searchParams.get('limit') ?? '100', 10)

  let query = supabase
    .from('jobs')
    .select('*, customer:customers(id,name,phone,email)')
    .order('created_at', { ascending: false })
    .limit(limit)

  if (status) query = query.eq('status', status)
  if (q) query = query.or(`device_make.ilike.%${q}%,device_model.ilike.%${q}%,reported_fault.ilike.%${q}%,imei.ilike.%${q}%`)

  const { data, error } = await query
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })
  return NextResponse.json({ jobs: data })
}

export async function POST(request: NextRequest) {
  const supabase = createAdminClient()

  try {
    const body = await request.json()
    const {
      customer_id,
      device_type,
      device_make,
      device_model,
      imei,
      reported_fault,
      password,
      backup_required,
      technician_name,
      quoted_price,
      notes,
      photo_urls = [],
    } = body

    if (!device_make || !device_model || !reported_fault) {
      return NextResponse.json({ error: 'device_make, device_model, and reported_fault are required' }, { status: 400 })
    }

    // Create job
    const { data: job, error: jobError } = await supabase
      .from('jobs')
      .insert({
        customer_id: customer_id || null,
        device_type: device_type || 'other',
        device_make,
        device_model,
        imei: imei || null,
        reported_fault,
        password: password || null,
        backup_required: Boolean(backup_required),
        technician_name: technician_name || null,
        quoted_price: quoted_price || null,
        notes: notes || null,
        status: 'intake',
      })
      .select()
      .single()

    if (jobError) return NextResponse.json({ error: jobError.message }, { status: 500 })

    // Attach photos if provided
    if (photo_urls.length > 0) {
      const photoInserts = photo_urls.map((url: string, idx: number) => ({
        job_id: job.id,
        url,
        photo_type: idx === 0 ? 'intake' : 'damage',
      }))
      await supabase.from('job_photos').insert(photoInserts)
    }

    return NextResponse.json({ job }, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 })
  }
}
