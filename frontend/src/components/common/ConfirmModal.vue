<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    type?: 'danger' | 'primary' | 'warning'
  }>(),
  {
    title: '✨ 温馨提示',
    message: '确定要执行此操作吗？',
    confirmText: '确定',
    cancelText: '取消',
    type: 'primary'
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const modalRef = ref<HTMLElement | null>(null)
let mouseDownOnBackdrop = false

function handleMouseDown(e: MouseEvent) {
  mouseDownOnBackdrop = e.target === modalRef.value
}

function handleClick(e: MouseEvent) {
  if (e.target === modalRef.value && mouseDownOnBackdrop) {
    handleClose()
  }
  mouseDownOnBackdrop = false
}

function handleClose() {
  emit('update:modelValue', false)
  emit('cancel')
}

function handleConfirm() {
  emit('confirm')
  emit('update:modelValue', false)
}

function handleKeyDown(e: KeyboardEvent) {
  if (props.modelValue && e.key === 'Escape') {
    handleClose()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      ref="modalRef"
      class="modal-backdrop-custom"
      @mousedown="handleMouseDown"
      @click="handleClick"
    >
      <div class="modal-dialog-custom confirm-box" @click.stop>
        <div class="modal-header-confirm">
          <span>{{ title || '✨ 温馨提示' }}</span>
        </div>

        <p class="confirm-message">
          {{ message }}
        </p>

        <slot />

        <div class="confirm-actions">
          <button type="button" class="btn-cancel" @click="handleClose">
            {{ cancelText }}
          </button>
          <button
            type="button"
            class="btn-confirm"
            :class="{
              'btn-danger-confirm': type === 'danger',
              'btn-warning-confirm': type === 'warning',
              'btn-primary-confirm': type === 'primary'
            }"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  z-index: 2500;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.confirm-box {
  width: 100%;
  max-width: 380px;
  background: #0d1b31 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5) !important;
  box-sizing: border-box;
}

:root.theme-light-warm .confirm-box,
:root.theme-nordic-cool .confirm-box,
:root.theme-sakura-peach .confirm-box,
:root.theme-autumn-maple .confirm-box,
:root.theme-macaron-pink .confirm-box,
:root.theme-macaron-blue .confirm-box,
:root.theme-macaron-green .confirm-box,
:root.theme-macaron-yellow .confirm-box,
:root.theme-macaron-purple .confirm-box,
:root.theme-macaron-orange .confirm-box {
  background: #ffffff !important;
  border: 1px solid rgba(0, 0, 0, 0.12) !important;
}

.modal-header-confirm {
  display: flex;
  justify-content: center;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 12px;
}

.confirm-message {
  font-size: 0.88rem;
  color: var(--text-main);
  margin: 12px 0 20px 0;
  line-height: 1.6;
  text-align: center;
}

.confirm-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 20px;
}

.btn-cancel {
  width: 90px;
  height: 36px;
  padding: 0;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
  color: var(--text-main);
  border-radius: 8px;
  font-weight: 800;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-confirm {
  width: 90px;
  height: 36px;
  padding: 0;
  border-radius: 8px;
  font-weight: 800;
  font-size: 0.85rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  color: #fff;
}

.btn-danger-confirm {
  background: #ef4444;
  border: 1px solid #ef4444;
  box-shadow: 0 4px 10px rgba(239, 68, 68, 0.25);
}

.btn-danger-confirm:hover {
  background: #dc2626;
}

.btn-primary-confirm {
  background: #7c3aed;
  border: 1px solid #7c3aed;
  box-shadow: 0 4px 10px rgba(124, 58, 237, 0.25);
}

.btn-primary-confirm:hover {
  background: #6d28d9;
}

.btn-warning-confirm {
  background: #f59e0b;
  border: 1px solid #f59e0b;
  box-shadow: 0 4px 10px rgba(245, 158, 11, 0.25);
}
</style>
