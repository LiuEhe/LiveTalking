import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import ChatView from '../views/ChatView.vue'
import AvatarView from '../views/AvatarView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: HomeView
        },
        {
            path: '/chat',
            name: 'chat',
            component: ChatView
        },
        {
            path: '/avatar',
            name: 'avatar',
            component: AvatarView
        }
        // 以后需要添加新页面，继续在这里以对象形式补充即可
    ]
})

export default router
