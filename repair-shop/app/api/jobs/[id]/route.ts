import { NextResponse, type NextRequest } from 'next/server'
import { createAdminClient } from '@/lib/supabase/server'

export async function GET(_: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = createAdminClient()

  const { data, error } = await supabase
    .from('jobs')
    .select('*, customer:customers(id,name,phone,email), photos:job_photos(*), signature:signatures(*), parts:job_parts(*)')
    .eq('id', id)
    .single()

  if (error || !data) return NextResponse.json({ error: 'Job not found' }, { status: 404 })
  return NextResponse.json({ job: data })
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = createAdminClient()

  try {
    const body = await request.json()
    const { add_part, ...jobFields } = body

    // Handle adding a part
    if (add_part) {
      const { inventory_id, part_name, quantity, unit_price } = add_part

      // Insert job_part record
      await supabase.from('job_parts').insert({
        job_id: id,
        inventory_id: inventory_id || null,
        part_name,
        quantity: quantity || 1,
        unit_price: unit_price || null,
      })

      // Decrement inventory quantity
      if (inventory_id) {
        const { data: inv } = await supabase
          .from('inventory')
          .select('quantity')
          .eq('id', inventory_id)
          .single()

        if (inv) {
          await supabase
            .from('inventory')
            .update({ quantity: Math.max(0, inv.quantity - (quantity || 1)) })
            .eq('id', inventory_id)
        }
      }

      const { data: parts } = await supabase.from('job_parts').select('*').eq('job_id', id)
      return NextResponse.json({ parts })
    }

    // Update job fields
    const allowedFields: Record<string, unknown> = {}
    const allowed = ['internal_notes', 'notes', 'final_price', 'technician_name', 'quoted_price', 'backup_completed']
    for (const key of allowed) {
      if (key in jobFields) allowedFields[key] = jobFields[key]
    }

    const { data, error } = await supabase
      .from('jobs')
      .update(allowedFields)
      .eq('id', id)
      .select('*, customer:customers(id,name,phone,email), photos:job_photos(*), signature:signatures(*), parts:job_parts(*)')
      .single()

    if (error) return NextResponse.json({ error: error.message }, { status: 500 })
    return NextResponse.json({ job: data })
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 })
  }
}
