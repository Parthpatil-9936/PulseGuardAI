/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base tokens
        background: '#F8FAFC',
        surface: {
          DEFAULT: '#FFFFFF',
          glass: 'rgba(255, 255, 255, 0.6)',
        },
        // Primary brand tokens
        primary: {
          DEFAULT: '#0EA5B7',
          500: '#0EA5B7',
          600: '#0D8A9A',
        },
        'teal-500': '#0EA5B7',
        'teal-600': '#0D8A9A',
        // Secondary tokens
        secondary: {
          DEFAULT: '#3B82F6',
          500: '#3B82F6',
        },
        'blue-500': '#3B82F6',
        // Alert tiers tokens
        alert: {
          'tier1-red': '#EF4444',
          'tier2-amber': '#F59E0B',
          'tier3-muted': '#94A3B8',
        },
        'tier1-red': '#EF4444',
        'tier2-amber': '#F59E0B',
        'tier3-muted': '#94A3B8',
        // Typography / text tokens
        text: {
          heading: '#0F172A',
          body: '#475569',
          muted: '#94A3B8',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 30px rgba(0, 0, 0, 0.08)',
        'elevated': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03)',
        'elevated-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 10px 10px -5px rgba(0, 0, 0, 0.02)',
      },
      animation: {
        'mesh-drift-1': 'drift1 20s ease-in-out infinite alternate',
        'mesh-drift-2': 'drift2 25s ease-in-out infinite alternate',
        'mesh-drift-3': 'drift3 22s ease-in-out infinite alternate',
        'subtle-pulse': 'subtlePulse 3s ease-in-out infinite',
        'alert-beacon': 'alertBeacon 1.5s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        drift1: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '100%': { transform: 'translate(80px, 50px) scale(1.1)' },
        },
        drift2: {
          '0%': { transform: 'translate(0px, 0px) scale(1.05)' },
          '100%': { transform: 'translate(-70px, 80px) scale(0.95)' },
        },
        drift3: {
          '0%': { transform: 'translate(0px, 0px) scale(0.95)' },
          '100%': { transform: 'translate(50px, -60px) scale(1.15)' },
        },
        subtlePulse: {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '0.85', transform: 'scale(1.02)' },
        },
        alertBeacon: {
          '0%': { transform: 'scale(0.95)', opacity: '0.8' },
          '50%': { transform: 'scale(1.15)', opacity: '1' },
          '100%': { transform: 'scale(0.95)', opacity: '0.8' },
        }
      }
    },
  },
  plugins: [],
}
