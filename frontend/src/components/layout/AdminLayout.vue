<script setup lang="ts">
import SidebarNav from './SidebarNav.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
</script>

<template>
  <div class="app-layout">
    <SidebarNav />
    <div class="main-wrapper">
      <main class="main-content">
        <router-view />
      </main>
    </div>
    <ToastContainer />
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  width: 100%;
  min-height: 100vh;
  background: var(--bg-gradient);
  color: var(--text-main);
}

.main-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
  width: 100%;
}

.main-content {
  flex: 1;
  padding: 25px 35px;
  width: 100%;
  box-sizing: border-box;
}
</style>
