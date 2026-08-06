import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Internal dashboard theme (staff tool — unchanged)
        bg: '#09090b',
        surface: '#18181b',
        'surface-2': '#27272a',
        border: '#3f3f46',
        primary: '#dc2626',
        'primary-hover': '#b91c1c',
        'primary-muted': '#450a0a',
        fg: '#fafafa',
        muted: '#a1a1aa',
        success: '#22c55e',
        warning: '#f59e0b',
        info: '#3b82f6',

        // Public site brand palette — dark, technical, blue-accented
        brand: {
          bg: '#05070C',
          'bg-alt': '#090D16',
          surface: '#0E1422',
          'surface-2': '#111A2C',
          border: 'rgba(90,145,255,0.16)',
          'border-strong': 'rgba(90,145,255,0.32)',
          blue: '#2F6BFF',
          'blue-bright': '#5B8DFF',
          white: '#F4F7FC',
          muted: '#8D96AC',
          'muted-2': '#5E6780',
          green: '#3DDC97',
          amber: '#FF9F5B',
        },
      },
      fontFamily: {
        sans: ['var(--font-body)', 'Inter', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Space Grotesk', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(180deg, #5B8DFF, #2F6BFF)',
        'brand-grid': `linear-gradient(rgba(90,145,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(90,145,255,0.06) 1px, transparent 1px)`,
        'brand-glow': 'radial-gradient(closest-side, rgba(47,107,255,0.25), transparent 70%)',
      },
      backgroundSize: {
        grid: '56px 56px',
      },
      animation: {
        'pulse-red': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

export default config
