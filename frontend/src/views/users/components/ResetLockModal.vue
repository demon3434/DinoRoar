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

const dinosaurs = [
  { id: 1, name: '霸王龙', img: '/static/images/dinosaurs/t_rex.webp' },
  { id: 2, name: '三角龙', img: '/static/images/dinosaurs/triceratops.webp' },
  { id: 3, name: '剑龙', img: '/static/images/dinosaurs/stegosaurus.webp' },
  { id: 4, name: '翼手龙', img: '/static/images/dinosaurs/pterodactyl.webp' },
  { id: 5, name: '腕龙', img: '/static/images/dinosaurs/brachiosaurus.webp' }
]

const currentSelectedDinos = ref<number[]>([])
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
      currentSelectedDinos.value = []
    }
  }
)

function addDinoToSequence(id: number) {
  if (currentSelectedDinos.value.length >= 3) {
    return
  }
  currentSelectedDinos.value.push(id)
}

function clearDinoSequence() {
  currentSelectedDinos.value = []
}

function getDinoObj(id: number) {
  return dinosaurs.find((d) => d.id === id)
}

async function handleResetLock() {
  if (!props.user) return
  if (currentSelectedDinos.value.length !== 3) {
    showToast('请先选择3个恐龙', 'warning')
    return
  }

  const pattern = currentSelectedDinos.value.join(',')
  loading.value = true
  try {
    await apiClient.post(`/api/admin/users/${props.user.id}/reset-lock`, {
      lock_pattern: pattern
    })
    showToast('解锁码重置指令挂载成功！手机端下一次同步时生效', 'success')
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
      <div class="modal-dialog-custom" style="max-width: 480px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            重置解锁序列 - {{ user?.username }}
          </span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px;">
          请点击选择 3 个恐龙，为孩子设置手势解锁序列。孩子端仅提示恐龙顺序，数字不对外显示。
        </p>

        <!-- 5 只恐龙选择网格 -->
        <div class="dino-selection-grid">
          <button
            v-for="d in dinosaurs"
            :key="d.id"
            type="button"
            class="dino-btn"
            :title="d.name"
            @click="addDinoToSequence(d.id)"
          >
            <div class="dino-img-box">
              <img :src="d.img" :alt="d.name" />
            </div>
            <span>{{ d.name }}({{ d.id }})</span>
          </button>
        </div>

        <!-- 预览已选序列 -->
        <label class="form-label" style="text-align: center; display: block; margin-top: 15px; margin-bottom: 6px;">
          已选解锁序列 (前 3 次有效)
        </label>
        <div class="dino-preview-seq">
          <div
            v-for="idx in [0, 1, 2]"
            :key="idx"
            class="dino-preview-item"
            :class="{ filled: idx < currentSelectedDinos.length }"
          >
            <img
              v-if="idx < currentSelectedDinos.length && getDinoObj(currentSelectedDinos[idx])"
              :src="getDinoObj(currentSelectedDinos[idx])?.img"
              :alt="getDinoObj(currentSelectedDinos[idx])?.name"
              :title="getDinoObj(currentSelectedDinos[idx])?.name"
              style="width: 100%; height: 100%; object-fit: cover; border-radius: 8px;"
            />
          </div>
        </div>

        <div style="text-align: center; font-size: 1.1rem; font-weight: 700; margin-top: 5px; color: var(--primary, #8b5cf6);">
          数字序列：<span>{{ currentSelectedDinos.join(', ') || '-' }}</span>
        </div>

        <div style="margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--card-border); display: flex; justify-content: flex-end; gap: 10px;">
          <button type="button" class="btn-outline-purple" style="padding: 6px 16px; border-radius: 8px; font-weight: 700;" @click="clearDinoSequence">清空</button>
          <button type="button" class="btn-outline-purple" style="padding: 6px 16px; border-radius: 8px; font-weight: 700;" @click="handleClose">取消</button>
          <button
            type="button"
            class="btn btn-primary-purple"
            :disabled="currentSelectedDinos.length !== 3 || loading"
            :style="currentSelectedDinos.length !== 3 ? 'opacity: 0.5; cursor: not-allowed;' : ''"
            style="padding: 6px 20px; border-radius: 8px; font-weight: 700;"
            @click="handleResetLock"
          >
            确定重置
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
