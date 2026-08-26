/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cisco: {
          blue: "#049fd9",
          dark: "#002c3d",
          accent: "#6cc04a",
        }
      }
    },
  },
  plugins: [],
}
