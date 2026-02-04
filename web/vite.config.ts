import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { compilerOptions } from 'vue3-pixi'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  const API_TARGET = env.VITE_API_TARGET || 'http://localhost:8002'
  const WS_TARGET = env.VITE_WS_TARGET || 'ws://localhost:8002'

  return {
    plugins: [
      vue({
        template: {
          compilerOptions,
        },
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src')
      }
    },
    build: {
      assetsDir: 'web_static', // 避免与游戏原本的 /assets 目录冲突
    },
    server: {
      host: '0.0.0.0', // 允许局域网访问
      proxy: {
        '/api': {
          target: API_TARGET,
          changeOrigin: true,
        },
        '/ws': {
          target: WS_TARGET,
          ws: true,
          changeOrigin: true,
        },
        '/assets': {
          target: API_TARGET,
          changeOrigin: true,
        }
      }
    }
  }
})
