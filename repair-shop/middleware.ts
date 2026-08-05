import { NextResponse, type NextRequest } from 'next/server'
import { createServerClient, type CookieOptions } from '@supabase/ssr'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Staff-only UI routes and the API endpoints they use for managing
  // customers/inventory/job lists. Per-job endpoints (`/api/jobs/[id]`,
  // `/api/jobs/[id]/status`, `/api/upload`) stay open — the public
  // /collect/[id] signature page relies on them for unauthenticated
  // customers picking up their device.
  const protectedPagePrefixes = ['/dashboard', '/jobs', '/customers', '/inventory']
  const protectedApiPrefixes = ['/api/customers', '/api/inventory']

  const isProtectedPage = protectedPagePrefixes.some((r) => pathname.startsWith(r))
  const isProtectedApi = pathname === '/api/jobs' || protectedApiPrefixes.some((r) => pathname.startsWith(r))
  const isLogin = pathname === '/login'

  // The public marketing site, the customer collect flow, and per-job API
  // routes don't need Supabase at all — skip it entirely so the site keeps
  // working even when Supabase env vars aren't configured.
  if (!isProtectedPage && !isProtectedApi && !isLogin) {
    return NextResponse.next()
  }

  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  if (!user && (isProtectedPage || isProtectedApi)) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  if (user && isLogin) {
    const url = request.nextUrl.clone()
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
