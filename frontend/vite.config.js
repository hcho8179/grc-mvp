import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    port: 5173,
    proxy: {
      // All /api/* calls forwarded to FastAPI at :8000 unchanged
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
