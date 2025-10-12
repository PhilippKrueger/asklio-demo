/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'Courier New', 'monospace'],
      },
      colors: {
        black: '#000000',
        white: '#FFFFFF',
      },
      borderWidth: {
        '3': '3px',
        '4': '4px',
      },
      transitionDuration: {
        '100': '100ms',
        '150': '150ms',
      },
    },
  },
  plugins: [],
}

