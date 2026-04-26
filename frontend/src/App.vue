<template>
  <Navbar />
  <main class="pt-16 min-h-screen">
    <router-view />
  </main>
</template>

<script setup lang="ts">
import Navbar from './components/Navbar.vue'
</script>

<style scoped>
/* Global layout styles if needed */
</style>
