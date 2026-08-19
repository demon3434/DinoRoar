<script setup lang="ts">
import { toastState } from '@/utils/toast'
</script>

<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div
        v-for="item in toastState.items"
        :key="item.id"
        class="toast-item"
        :class="item.type"
      >
        <span>{{ item.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  pointer-events: none;
}

.toast-item {
  pointer-events: auto;
  background: #0f172af2;
  border: 1px solid var(--primary, #8b5cf6);
  color: #ffffff;
  padding: 10px 24px;
  border-radius: 12px;
  font-size: 0.92rem;
  font-weight: 700;
  box-shadow: 0 8px 30px rgba(139, 92, 246, 0.35);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.toast-item.success {
  border-color: var(--dino-green, #22c55e);
  box-shadow: 0 8px 30px rgba(34, 197, 94, 0.35);
}

.toast-item.error {
  border-color: var(--dino-red, #ef4444);
  box-shadow: 0 8px 30px rgba(239, 68, 68, 0.35);
}

.toast-item.warning {
  border-color: #f59e0b;
  box-shadow: 0 8px 30px rgba(245, 158, 11, 0.35);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.toast-enter-from {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}
</style>
