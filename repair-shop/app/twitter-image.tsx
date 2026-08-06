import { ImageResponse } from 'next/og'

export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          background: '#05070C',
          backgroundImage: 'radial-gradient(circle at 82% 12%, rgba(47,107,255,0.35), transparent 60%)',
          padding: '80px 90px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginBottom: 40 }}>
          <div
            style={{
              display: 'flex',
              width: 64,
              height: 64,
              borderRadius: 14,
              background: '#0E1422',
              border: '1px solid rgba(90,145,255,0.32)',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#5B8DFF" strokeWidth="2.2" strokeLinecap="round">
              <path d="M5 12.55a11 11 0 0 1 14.08 0" />
              <path d="M1.42 9a16 16 0 0 1 21.16 0" />
              <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
              <circle cx="12" cy="20" r="1.6" fill="#5B8DFF" stroke="none" />
            </svg>
          </div>
          <div style={{ display: 'flex', fontSize: 44, fontWeight: 700 }}>
            <span style={{ color: '#5B8DFF' }}>404</span>
            <span style={{ color: '#F4F7FC', marginLeft: 14 }}>FIXED</span>
          </div>
        </div>
        <div style={{ display: 'flex', fontSize: 56, fontWeight: 700, color: '#F4F7FC', lineHeight: 1.15, maxWidth: 920 }}>
          IT problems don&apos;t wait. Neither do we.
        </div>
        <div style={{ display: 'flex', marginTop: 30, fontSize: 28, color: '#8D96AC' }}>
          IT Support · Network Installs · WiFi Help — Cardiff &amp; Penarth
        </div>
      </div>
    ),
    { ...size }
  )
}
