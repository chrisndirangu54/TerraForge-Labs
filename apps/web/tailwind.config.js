/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        forge: {
          950: '#080c0a',
          900: '#0f1612',
          850: '#141d18',
          800: '#1a241e',
          700: '#243028',
          600: '#2f3d34',
          500: '#3d4f44',
        },
        ore: {
          600: '#9a5c38',
          500: '#c4784a',
          400: '#d4926a',
          300: '#e8b08a',
        },
        mineral: {
          600: '#2d6b6b',
          500: '#4a9b9b',
          400: '#6bb8b8',
          300: '#8fd4d4',
        },
        strata: {
          500: '#9a8548',
          400: '#b8a56a',
          300: '#d4c48a',
        },
        moss: {
          600: '#3d5c38',
          500: '#5a7a52',
        },
        sediment: {
          DEFAULT: '#e6e2d8',
          muted: '#9a9488',
          dim: '#6b7368',
        },
      },
      fontFamily: {
        display: ['Rajdhani', 'system-ui', 'sans-serif'],
        sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(74, 155, 155, 0.15)',
        'glow-ore': '0 0 24px rgba(196, 120, 74, 0.2)',
        'glow-lg': '0 0 40px rgba(74, 155, 155, 0.12), 0 8px 32px rgba(0, 0, 0, 0.4)',
        panel: '0 4px 24px rgba(0, 0, 0, 0.35)',
        'panel-hover': '0 8px 32px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(74, 155, 155, 0.08)',
        glass: 'inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 4px 24px rgba(0, 0, 0, 0.3)',
      },
      backgroundImage: {
        'terrain-grid':
          'linear-gradient(rgba(74, 155, 155, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(74, 155, 155, 0.04) 1px, transparent 1px)',
        'contour-lines':
          'repeating-radial-gradient(ellipse 80% 50% at 50% 100%, transparent 0, transparent 38px, rgba(74, 155, 155, 0.03) 38px, rgba(74, 155, 155, 0.03) 39px)',
        'strata-gradient':
          'linear-gradient(165deg, rgba(196, 120, 74, 0.08) 0%, transparent 40%, rgba(74, 155, 155, 0.06) 100%)',
        'hero-gradient':
          'radial-gradient(ellipse 80% 60% at 20% 40%, rgba(196, 120, 74, 0.15), transparent), radial-gradient(ellipse 60% 50% at 80% 60%, rgba(74, 155, 155, 0.12), transparent)',
        'card-shine':
          'linear-gradient(105deg, transparent 40%, rgba(255, 255, 255, 0.03) 50%, transparent 60%)',
      },
      backgroundSize: {
        grid: '32px 32px',
        contour: '100% 100%',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.5s ease-out forwards',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
        shimmer: 'shimmer 2.5s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
    },
  },
  plugins: [],
};