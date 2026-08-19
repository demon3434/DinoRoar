<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  modelValue: boolean
  user: { id: number; username: string } | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'success'): void
}>()

const password = ref('')
const loading = ref(false)

let mouseDownOnBackdrop = false

function onBackdropMouseDown(e: MouseEvent) {
  mouseDownOnBackdrop = e.target === e.currentTarget
}

function onBackdropClick(e: MouseEvent, closeFn: () => void) {
  if (mouseDownOnBackdrop && e.target === e.currentTarget) {
    closeFn()
  }
  mouseDownOnBackdrop = false
}

function handleClose() {
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      password.value = ''
    }
  }
)

async function handleResetPassword() {
  if (!props.user) return
  const p = password.value.trim()

  if (!p) {
    showToast('请输入新密码', 'warning')
    return
  }

  loading.value = true
  try {
    await apiClient.post(`/api/admin/users/${props.user.id}/reset-password`, {
      new_password: p
    })
    showToast('密码重置成功！', 'success')
    handleClose()
    emit('success')
  } catch (err: any) {
    showToast(err.response?.data?.detail || '重置失败', 'error')
  } finally {
    loading.value = false
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) {
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
      class="modal"
      style="display: flex; z-index: 1000;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick($event, handleClose)"
    >
      <div class="modal-dialog-custom" style="max-width: 440px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            重置密码 - {{ user?.username }}
          </span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <form style="display: flex; flex-direction: column; gap: 14px;" @submit.prevent="handleResetPassword">
          <div class="form-group" style="margin: 0;">
            <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; color: var(--text-main);">
              新安全密码
            </label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              placeholder="输入新的六位以上密码"
              required
              style="height: 38px; font-size: 0.88rem;"
            />
          </div>

          <div style="margin-top: 10px; padding-top: 14px; border-top: 1px solid var(--card-border); display: flex; justify-content: flex-end; gap: 12px;">
            <button type="button" class="btn-outline-purple" style="padding: 6px 18px; border-radius: 8px; font-weight: 700;" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary-purple" :disabled="loading" style="padding: 6px 20px; border-radius: 8px; font-weight: 700;">确定重置</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
