/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#fbf8ff',
          container: {
            lowest: '#ffffff',
            low: '#f4f2fd',
            mid: '#ece8f7',
          }
        },
        primary: {
          DEFAULT: '#3525cd',
          container: '#4f46e5',
          dark: '#2416a8',
          'on-primary': '#ffffff',
        },
        secondary: {
          DEFAULT: '#006c49',
          container: '#86f8c4',
          dark: '#005236',
          'on-secondary': '#ffffff',
        },
        tertiary: {
          DEFAULT: '#825300',
          fixed: '#ffddb8',
          'on-tertiary-fixed-variant': '#653e00',
        },
        error: {
          DEFAULT: '#ba1a1a',
          container: '#ffdad6',
          dark: '#93000a',
        },
        outline: {
          DEFAULT: '#757780',
          variant: '#c5c6d3',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
      boxShadow: {
        'xs': '0 1px 2px 0 rgba(0, 0, 0, 0.04)',
        'hairline': '0 0 0 1px rgba(0, 0, 0, 0.06)',
      }
    },
  },
  plugins: [],
}
