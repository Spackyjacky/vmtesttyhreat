import { ImageResponse } from 'next/og'

export const size = { width: 32, height: 32 }
export const contentType = 'image/png'

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#05070C',
          borderRadius: 7,
        }}
      >
        <svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="#5B8DFF" strokeWidth="2.6" strokeLinecap="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0" />
          <path d="M1.42 9a16 16 0 0 1 21.16 0" />
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
          <circle cx="12" cy="20" r="1.6" fill="#5B8DFF" stroke="none" />
        </svg>
      </div>
    ),
    { ...size }
  )
}
