import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        aegis: {
          bg:       '#080c14',
          surface:  '#0d1421',
          card:     '#111827',
          border:   '#1e293b',
          accent:   '#00d4ff',
          danger:   '#ff3b5c',
          warn:     '#f59e0b',
          success:  '#10b981',
          muted:    '#64748b',
          glow:     '#00d4ff33',
        },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      backgroundImage: {
        'grid-pattern': "url(\"data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%231e293b' fill-opacity='0.4'%3E%3Cpath d='M0 0h40v1H0zM0 0h1v40H0z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
      },
      animation: {
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-ping':   'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'scan-line':   'scan 4s linear infinite',
      },
      keyframes: {
        scan: {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
      boxShadow: {
        'glow-accent': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-danger': '0 0 20px rgba(255, 59, 92, 0.3)',
        'card':        '0 4px 24px rgba(0, 0, 0, 0.4)',
      },
    },
  },
  plugins: [],
}
export default config
