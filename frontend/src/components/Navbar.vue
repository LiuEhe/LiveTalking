<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/80">
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center relative">
      <!-- Logo/Brand (Left Aligned) -->
      <div class="flex items-center gap-2 z-10">
        <div class="w-8 h-8 bg-linear-to-tr from-indigo-600 to-violet-600 rounded-lg flex items-center justify-center shadow-indigo-200">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zm-1 9a1 1 0 00-1 1v-4a1 1 0 102 0v4a1 1 0 00-1 1z" clip-rule="evenodd" />
          </svg>
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
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            对话
          </router-link>
          <router-link 
            to="/avatar" 
            class="px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-2"
            active-class="bg-gray-900 text-white shadow-sm"
            inactive-class="text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            形象管理
          </router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
// No complex logic needed for the basic Navbar
</script>

<style scoped>
/* Glassmorphism subtle polish */
nav :deep(.router-link-active) {
  transform: translateY(-1px);
}
</style>
