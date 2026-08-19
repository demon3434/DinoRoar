<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  modelValue: boolean
  imageUrl: string
  title: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

const scale = ref(1)

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      scale.value = 1
    }
  }
)

function zoomIn() {
  scale.value = Math.min(scale.value + 0.25, 3.0)
}

function zoomOut() {
  scale.value = Math.max(scale.value - 0.25, 0.5)
}

function resetZoom() {
  scale.value = 1
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
      class="modal lightbox-modal"
      style="display: flex; z-index: 1500; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px);"
      @click="handleClose"
    >
      <div
        style="position: relative; max-width: 90vw; max-height: 90vh; display: flex; flex-direction: column; align-items: center; justify-content: center;"
        @click.stop
      >
        <!-- Lightbox 顶部控制栏 -->
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; color: #fff;">
          <span style="font-weight: 700; font-size: 1rem;">🖼️ {{ title }}</span>
          <div style="display: flex; gap: 10px; align-items: center;">
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="zoomIn">放大 🔍+</button>
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="zoomOut">缩小 🔍-</button>
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="resetZoom">1:1 重置</button>
            <span class="modal-close-icon" title="关闭" style="margin-left: 8px;" @click="handleClose">✕</span>
          </div>
        </div>

        <!-- 大图展示区 -->
        <div style="overflow: auto; max-width: 100%; max-height: 80vh; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: #09090b; display: flex; align-items: center; justify-content: center; padding: 10px;">
          <img
            :src="imageUrl"
            :style="{ transform: `scale(${scale})`, transition: 'transform 0.15s ease-out' }"
            style="max-width: 80vw; max-height: 75vh; object-fit: contain; transform-origin: center center;"
            alt="Full size canvas"
          />
        </div>
      </div>
    </div>
  </Teleport>
</template>
