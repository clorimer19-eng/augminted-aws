/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        beige: {
          50: '#FBFBF9',
          100: '#F5F5F0', // Main background
          200: '#EBEBE6',
          300: '#DCDCD6',
        },
        green: {
          50: '#F0F9F2',
          100: '#E6F4EA', // Success badge bg
          600: '#1E8E3E', // Success text
          700: '#137333',
        },
        brown: {
          500: '#B08D55', // Gold/Brown accent
          600: '#9C7B46',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
