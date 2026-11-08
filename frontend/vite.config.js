import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/predict': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/complaints': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/history': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/summarize': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
