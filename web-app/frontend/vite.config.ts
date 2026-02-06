import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    // 本番ビルドの最適化
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router'],
          charts: ['chart.js', 'vue-chartjs'],
          utils: ['axios', 'marked', 'html2canvas', 'file-saver']
        }
      }
    }
  },
  // 本番環境のベースURL設定
  base: process.env.NODE_ENV === 'production' ? '/' : '/',
  server: {
    host: '0.0.0.0',
    port: 3000
  }
})