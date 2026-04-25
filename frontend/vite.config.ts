// Vite 开发配置。
// 这份配置最重要的点，是把前端 `/api` 请求代理到后端 8010 端口。
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  server: {
    // 本地开发时直接访问 127.0.0.1:3000，接口请求再转发到后端。
    host: '127.0.0.1', // 瑙ｅ喅鐢变簬 localhost 閫犳垚鐨勬棤娉曡闂棶棰?
    open: true,         // 鍚姩鍚庤嚜鍔ㄦ墦寮€娴忚鍣?
    port: 3000,         // 鎸囧畾绔彛
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true
      }
    }
  }
})
