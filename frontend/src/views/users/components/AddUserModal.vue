<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'success'): void
}>()

const username = ref('')
const nickname = ref('')
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
      username.value = ''
      nickname.value = ''
      password.value = ''
    }
  }
)

async function handleAddUser() {
  const u = username.value.trim()
  const n = nickname.value.trim()
  const p = password.value.trim()

  if (!u) {
    showToast('请填写用户名', 'warning')
    return
  }

  loading.value = true
  try {
    await apiClient.post('/api/admin/users', {
      username: u,
      nickname: n || null,
      password: p || '123456'
    })
    showToast('新增孩子账户成功！', 'success')
    handleClose()
    emit('success')
  } catch (err: any) {
    showToast(err.response?.data?.detail || '创建失败', 'error')
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
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">新增孩子账户</span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <form style="display: flex; flex-direction: column; gap: 14px;" @submit.prevent="handleAddUser">
          <div class="form-group" style="margin: 0;">
            <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; color: var(--text-main);">
              账户名称
            </label>
            <input
              v-model="username"
              type="text"
              class="form-control"
              placeholder="孩子名字拼音，如 highdino"
              required
              style="height: 38px; font-size: 0.88rem;"
            />
          </div>

          <div class="form-group" style="margin: 0;">
            <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; color: var(--text-main);">
              昵称 (显示名称)
            </label>
            <input
              v-model="nickname"
              type="text"
              class="form-control"
              placeholder="显示名字，如 宝贝、小恐龙"
              style="height: 38px; font-size: 0.88rem;"
            />
          </div>

          <div class="form-group" style="margin: 0;">
            <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.85rem; font-weight: 700; color: var(--text-main);">
              初始安全密码
            </label>
            <input
              v-model="password"
              type="password"
              class="form-control"
              placeholder="留空则默认为 123456"
              style="height: 38px; font-size: 0.88rem;"
            />
          </div>

          <div style="margin-top: 10px; padding-top: 14px; border-top: 1px solid var(--card-border); display: flex; justify-content: flex-end; gap: 12px;">
            <button type="button" class="btn-outline-purple" style="padding: 6px 18px; border-radius: 8px; font-weight: 700;" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary-purple" :disabled="loading" style="padding: 6px 20px; border-radius: 8px; font-weight: 700;">确定创建</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
