import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Use 127.0.0.1 explicitly — on Windows, 'localhost' resolves to IPv6 [::1]
// but uvicorn binds IPv4 only, causing ECONNREFUSED in the Vite proxy.
// Docker overrides this via the API_TARGET env var (http://backend:8000).
const apiTarget = process.env.API_TARGET ?? 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
