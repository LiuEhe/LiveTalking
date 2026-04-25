// 前端应用入口：
// 1. 创建 Vue 应用
// 2. 注册路由
// 3. 挂载到 index.html 中的 #app 节点
import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'

// createApp(App).mount('#app')

const app = createApp(App)
app.use(router) // 注册 router 后，整个应用里才能使用 <router-link> / <router-view>。
app.mount('#app')
