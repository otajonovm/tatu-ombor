/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,ts}'],
  theme: {
    extend: {
      colors: {
        brand: '#315efb',
      },
      boxShadow: {
        soft: '0 12px 34px rgba(15, 23, 42, 0.08)',
      },
    },
  },
  plugins: [],
}
