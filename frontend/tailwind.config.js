/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          background: '#F8FAFC',
          surface: '#FFFFFF',
          'surface-glass': 'rgba(255, 255, 255, 0.6)',
        },
        primary: {
          50: '#F0FDFA',
          100: '#CCFBF1',
          200: '#99F6E4',
          300: '#5EEAD4',
          400: '#2DD4BF',
          500: '#0EA5B7', // Primary teal-500
          600: '#0D8A9A', // Primary teal-600
          700: '#0F766E',
          800: '#115E59',
          900: '#134E4A',
        },
        secondary: {
          500: '#3B82F6', // Secondary blue-500
          600: '#2563EB',
          700: '#1D4ED8',
        },
        tier: {
          1: '#EF4444', // Alert tier 1 - Red
          '1-light': '#FEE2E2',
          '1-border': '#F87171',
          2: '#F59E0B', // Alert tier 2 - Amber
          '2-light': '#FEF3C7',
          '2-border': '#FBBF24',
          3: '#94A3B8', // Alert tier 3 - Muted slate
          '3-light': '#F1F5F9',
          '3-border': '#CBD5E1',
          normal: '#0EA5B7', // Normal tier - Teal
          'normal-light': '#F0FDFA',
        },
        slate: {
          900: '#0F172A', // Headings
          600: '#475569', // Body
          400: '#94A3B8', // Muted
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 30px rgba(0, 0, 0, 0.08)',
        'elevated': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 10px 25px -3px rgba(0, 0, 0, 0.08)',
        'elevated-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.06), 0 20px 30px -4px rgba(0, 0, 0, 0.1)',
        'pulse-red': '0 0 0 0 rgba(239, 68, 68, 0.6)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'tier1-pulse': 'tier1Pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'mesh-drift': 'meshDrift 20s ease-in-out infinite alternate',
      },
      keyframes: {
        tier1Pulse: {
          '0%, 100%': {
            boxShadow: '0 0 0 0 rgba(239, 68, 68, 0.6), 0 8px 30px rgba(239, 68, 68, 0.2)',
            borderColor: '#EF4444',
          },
          '50%': {
            boxShadow: '0 0 0 8px rgba(239, 68, 68, 0), 0 8px 30px rgba(239, 68, 68, 0.35)',
            borderColor: '#DC2626',
          }
        },
        meshDrift: {
          '0%': {
            transform: 'translate(0px, 0px) scale(1)',
          },
          '50%': {
            transform: 'translate(30px, -20px) scale(1.08)',
          },
          '100%': {
            transform: 'translate(-20px, 20px) scale(0.95)',
          }
        }
      }
    },
  },
  plugins: [],
}
