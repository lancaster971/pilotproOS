import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
// TODO: Re-enable Unplugin Icons after container compatibility fix
// import Icons from 'unplugin-icons/vite'
// import { FileSystemIconLoader } from 'unplugin-icons/loaders'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // TODO: Icons configuration - temporarily disabled for container compatibility
    // Icons({
    //   autoInstall: true,
    //   customCollections: {
    //     'node': FileSystemIconLoader('./src/assets/nodeIcons/svg', svg =>
    //       svg.replace(/^<svg /, '<svg fill="currentColor" ')
    //     )
    //   }
    // })
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