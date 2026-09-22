/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        space: {
          950: '#000000',
          900: '#05070B',
          850: '#0A0E17',
          800: '#111726',
          700: '#1C2438',
          600: '#2D3748',
        },
        water: {
          cyan: '#00B4D8',
          blue: '#0077B6',
          deep: '#03045E',
        },
        flood: {
          magenta: '#FF0055',
          signal: '#FF3366',
          glow: 'rgba(255, 0, 85, 0.4)',
        },
        radar: {
          green: '#00FF66',
          amber: '#FFB800',
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'SF Mono', 'Roboto Mono', 'monospace'],
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderWidth: {
        'thin': '1px',
      }
    },
  },
  plugins: [],
}
