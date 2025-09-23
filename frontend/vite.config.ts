import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import Icons from 'unplugin-icons/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // Unplugin Icons - Now working with container dependencies
    Icons({
      autoInstall: true,
      compiler: 'vue3'
    })
  ],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    watch: {
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      port: 3000,
    },
    proxy: {
      '/api': {
        // ALWAYS use backend-dev for consistency
        target: 'http://pilotpros-backend-dev:3001',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Forward all cookies from browser to backend
            if (req.headers.cookie) {
              proxyReq.setHeader('cookie', req.headers.cookie);
            }
          });
        }
      }
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    sourcemap: true,
  },
})