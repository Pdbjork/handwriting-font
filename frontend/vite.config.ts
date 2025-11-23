import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://api:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'http://api:8000',
        ws: true,
        changeOrigin: true
      },
      '/download': {
        target: 'http://api:8000',
        changeOrigin: true
      }
    }
  }
})
