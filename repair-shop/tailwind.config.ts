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

        // Public site brand palette — light, professional, upmarket
        brand: {
          navy: '#0B1220',
          ink: '#0F172A',
          slate: '#54607A',
          mist: '#F6F8FB',
          line: '#E4E9F1',
          teal: '#0D9488',
          blue: '#2563EB',
          emerald: '#10B981',
          amber: '#C9962A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(115deg, #0D9488 0%, #2563EB 55%, #10B981 100%)',
        'brand-gradient-soft': 'linear-gradient(135deg, rgba(13,148,136,0.08) 0%, rgba(37,99,235,0.08) 55%, rgba(16,185,129,0.08) 100%)',
      },
      animation: {
        'pulse-red': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
}

export default config
