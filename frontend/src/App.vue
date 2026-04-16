<script setup lang="ts">
</script>

<template>
  <div class="fixed top-6 left-6 z-100 flex gap-3">
    <router-link to="/chat" class="px-4 py-2 bg-white/80 backdrop-blur-md border border-gray-200 rounded-full text-sm font-medium shadow-sm hover:shadow-md transition-all active:scale-95" active-class="!bg-black !text-white !border-black">
      对话
    </router-link>
    <router-link to="/avatar" class="px-4 py-2 bg-white/80 backdrop-blur-md border border-gray-200 rounded-full text-sm font-medium shadow-sm hover:shadow-md transition-all active:scale-95" active-class="!bg-black !text-white !border-black">
      形象管理
    </router-link>
  </div>
  <router-view />
</template>
