<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'

// Initialize and bind theme on root app mount
useThemeStore()
</script>

<template>
  <router-view />
</template>

<style>
/* Global baseline styles defined in src/styles/main.css */
</style>
