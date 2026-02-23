import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['dev.witold.ovh', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: false,
      },
    },
  },
})

