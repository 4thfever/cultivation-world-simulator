import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { compilerOptions } from 'vue3-pixi'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions,
      },
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8002',
        ws: true,
        changeOrigin: true,
      },
      '/assets': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      }
    }
  }
})
