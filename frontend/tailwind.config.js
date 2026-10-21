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
        paypal: {
          blue: '#003087',
          lightBlue: '#0070BA',
          accent: '#00CFDE',
          dark: '#001C38',
        },
        nexus: {
          bg: '#0B0F19',
          card: '#111827',
          border: '#1F2937',
          accent: '#6366F1',
          gold: '#F59E0B',
        }
      }
    },
  },
  plugins: [],
}
