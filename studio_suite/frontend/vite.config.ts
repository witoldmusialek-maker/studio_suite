import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:8000'
const devPort = Number(process.env.VITE_DEV_PORT || 5174)
const devHmrHost = process.env.VITE_HMR_HOST || 'localhost'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: devPort,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: devHmrHost,
      clientPort: devPort,
      port: devPort,
    },
    allowedHosts: ['dev2.witold.ovh', 'localhost', '127.0.0.1'],
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: false,
      },
    },
  },
})

