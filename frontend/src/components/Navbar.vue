<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/80">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center relative">
      <!-- Logo/Brand (Left Aligned) -->
      <div class="flex items-center gap-2 z-10">
        <div class="w-8 h-8 bg-linear-to-tr from-indigo-600 to-violet-600 rounded-lg flex items-center justify-center shadow-indigo-200">
          <Mic class="h-5 w-5 text-white" />
        </div>
        <span class="text-gray-900 font-bold tracking-tight text-lg">LiveTalking</span>
      </div>

      <!-- Navigation Links (Center Aligned) -->
      <div class="absolute inset-x-0 flex justify-center pointer-events-none">
        <div class="flex items-center gap-1 pointer-events-auto">
          <router-link 
            to="/chat" 
            class="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-2"
            active-class="bg-gray-900 text-white shadow-sm"
            inactive-class="text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <MessageSquare class="h-4 w-4" />
            对话
          </router-link>
          <router-link 
            to="/avatar" 
            class="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-2"
            active-class="bg-gray-900 text-white shadow-sm"
            inactive-class="text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <UserRound class="h-4 w-4" />
            形象管理
          </router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { MessageSquare, UserRound, Mic } from 'lucide-vue-next'
</script>

<style scoped>
/* Glassmorphism subtle polish */
nav :deep(.router-link-active) {
  transform: translateY(-1px);
}
</style>
