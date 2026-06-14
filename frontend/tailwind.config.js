/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Roboto Mono', 'monospace'],
      },
      colors: {
        primary: {
          500: '#6366F1',
          glow: '#8B5CF6',
        },
        glass: {
          base: 'rgba(0, 0, 0, 0.2)',
          widget: 'rgba(15, 23, 42, 0.4)',
          element: 'rgba(255, 255, 255, 0.05)',
        }
      },
      boxShadow: {
        'glass-widget': '0 8px 30px rgba(0,0,0,0.12)',
        'ai-glow': '0 0 20px rgba(139, 92, 246, 0.5)',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}
