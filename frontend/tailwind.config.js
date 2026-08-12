/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { 
    extend: {
      colors: {
        ink: '#12131A',
        panel: '#1C1E27',
        manila: '#E4D9BE',
        'redaction-red': '#C4433D',
        'alert-amber': '#D69A44',
        'verified-teal': '#3E9C8F',
        'off-white': '#EDEBE3',
      },
      fontFamily: {
        sans: ['"Source Sans 3"', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'monospace'],
      }
    } 
  },
  plugins: [],
}
