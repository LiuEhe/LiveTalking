<script setup lang="ts">
// 顶层应用组件本身很薄，只负责提供一个固定导航和路由出口。
</script>

<template>
  <div class="fixed top-6 left-6 z-100 flex gap-3">
    <!-- 这里是一个非常轻量的全局导航，点击后切换到不同页面组件 -->
    <router-link to="/chat" class="px-4 py-2 bg-white/80 backdrop-blur-md border border-gray-200 rounded-full text-sm font-medium shadow-sm hover:shadow-md transition-all active:scale-95" active-class="!bg-black !text-white !border-black">
      对话
    </router-link>
    <router-link to="/avatar" class="px-4 py-2 bg-white/80 backdrop-blur-md border border-gray-200 rounded-full text-sm font-medium shadow-sm hover:shadow-md transition-all active:scale-95" active-class="!bg-black !text-white !border-black">
      形象管理
    </router-link>
  </div>
  <!-- 当前匹配到的页面会渲染在这里 -->
  <router-view />
</template>
