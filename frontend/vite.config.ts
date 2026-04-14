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
    host: '127.0.0.1', // 解决由于 localhost 造成的无法访问问题
    open: true,         // 启动后自动打开浏览器
    port: 3000,         // 指定端口
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8010',
        changeOrigin: true
      }
    }
  }
})