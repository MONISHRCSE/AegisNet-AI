/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        aegis: {
          bg:      '#080c14',
          surface: '#0d1421',
          card:    '#111827',
          border:  '#1e293b',
          accent:  '#00d4ff',
          danger:  '#ff3b5c',
          warn:    '#f59e0b',
          success: '#10b981',
          muted:   '#64748b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        card:         '0 4px 24px rgba(0,0,0,0.4)',
        'glow-accent':'0 0 20px rgba(0,212,255,0.25)',
        'glow-danger':'0 0 20px rgba(255,59,92,0.25)',
      },
    },
  },
  plugins: [],
}
