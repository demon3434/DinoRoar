<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue: boolean
  user: { id: number; username: string; lock_pattern?: string } | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const dinoMap: Record<number, { name: string; img: string }> = {
  1: { name: '霸王龙', img: '/static/images/dinosaurs/t_rex.webp' },
  2: { name: '三角龙', img: '/static/images/dinosaurs/triceratops.webp' },
  3: { name: '剑龙', img: '/static/images/dinosaurs/stegosaurus.webp' },
  4: { name: '翼手龙', img: '/static/images/dinosaurs/pterodactyl.webp' },
  5: { name: '腕龙', img: '/static/images/dinosaurs/brachiosaurus.webp' }
}

const parsedSlots = computed(() => {
  const pattern = props.user?.lock_pattern || '1,2,3'
  const ids = pattern.split(',').map((s) => Number(s.trim()))
  return [0, 1, 2].map((idx) => {
    const id = ids[idx]
    return id && dinoMap[id] ? { id, ...dinoMap[id] } : null
  })
})

const sequenceText = computed(() => {
  const pattern = props.user?.lock_pattern || '1,2,3'
  const ids = pattern.split(',').map((s) => Number(s.trim()))
  return ids.map((id) => (dinoMap[id] ? dinoMap[id].name : '未知')).join(' -> ')
})

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
      <div class="modal-dialog-custom" style="max-width: 400px; text-align: center;" @click.stop>
        <div class="modal-header" style="justify-content: center; position: relative;">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            解锁序列 - {{ user?.username }}
          </span>
          <span class="modal-close-icon" title="关闭" style="position: absolute; right: 0; top: 0;" @click="handleClose">✕</span>
        </div>

        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 20px;">
          该账号在手机端需要按照以下恐龙顺序依次点击进行解锁：
        </p>

        <!-- 3 个恐龙展示槽位 -->
        <div class="dino-preview-seq" style="justify-content: center; gap: 20px; margin-bottom: 20px; display: flex;">
          <div
            v-for="(slot, idx) in parsedSlots"
            :key="idx"
            class="dino-preview-item"
            :class="{ filled: !!slot }"
            style="width: 64px; height: 64px;"
          >
            <img
              v-if="slot"
              :src="slot.img"
              :alt="slot.name"
              :title="slot.name"
              style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;"
            />
          </div>
        </div>

        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 25px; color: var(--primary, #8b5cf6);">
          {{ sequenceText }}
        </div>

        <div style="display: flex; justify-content: center; padding-top: 10px; border-top: 1px solid var(--card-border);">
          <button type="button" class="btn btn-primary-purple" style="padding: 6px 24px; border-radius: 8px; font-weight: 700;" @click="handleClose">
            关闭
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
