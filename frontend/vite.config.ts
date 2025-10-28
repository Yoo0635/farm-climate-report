import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Dev에서 /api 호출은 FastAPI(127.0.0.1:8000)로 프록시 → CORS 회피
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  build: { outDir: 'dist' }
})

