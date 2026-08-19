<script setup lang="ts">
import { ref, watch } from 'vue'
import { showToast } from '@/utils/toast'
import { UploadCloud, X } from 'lucide-vue-next'

const props = defineProps<{
  modelValue?: string | File | null
  initialUrl?: string
  accept?: string
  maxSizeMb?: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', file: File | null): void
  (e: 'change', file: File | null): void
}>()

const isDragging = ref(false)
const previewUrl = ref<string>(props.initialUrl || (typeof props.modelValue === 'string' ? props.modelValue : ''))
const fileInput = ref<HTMLInputElement | null>(null)

watch(
  () => props.initialUrl,
  (val) => {
    if (val && !props.modelValue) {
      previewUrl.value = val
    }
  }
)

function handleFile(file: File) {
  if (file) {
    if (props.maxSizeMb && file.size > props.maxSizeMb * 1024 * 1024) {
      showToast(`文件大小不能超过 ${props.maxSizeMb}MB`, 'warning')
      return
    }
    previewUrl.value = URL.createObjectURL(file)
    emit('update:modelValue', file)
    emit('change', file)
  }
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    handleFile(target.files[0])
  }
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
    handleFile(e.dataTransfer.files[0])
  }
}

function clearImage() {
  previewUrl.value = ''
  if (fileInput.value) fileInput.value.value = ''
  emit('update:modelValue', null)
  emit('change', null)
}
</script>

<template>
  <div class="uploader-container">
    <div
      class="upload-area"
      :class="{ 'is-dragging': isDragging, 'has-preview': !!previewUrl }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="onDrop"
      @click="fileInput?.click()"
    >
      <input
        ref="fileInput"
        type="file"
        class="hidden"
        :accept="accept || 'image/png,image/jpeg,image/webp'"
        @change="onFileChange"
      />

      <div v-if="previewUrl" class="preview-box">
        <img :src="previewUrl" alt="Upload Preview" class="preview-img" />
        <button type="button" class="btn-clear" @click.stop="clearImage">
          <X class="w-4 h-4" />
        </button>
      </div>

      <div v-else class="upload-placeholder">
        <UploadCloud class="w-8 h-8 text-blue-400" />
        <p class="placeholder-text">点击或拖拽图片上传</p>
        <span class="placeholder-hint">支持 PNG, JPG, WebP</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.uploader-container {
  width: 100%;
}

.upload-area {
  width: 100%;
  min-height: 120px;
  border: 2px dashed var(--input-border);
  border-radius: var(--radius-md);
  background: var(--input-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.upload-area:hover, .upload-area.is-dragging {
  border-color: var(--primary);
  background: rgba(59, 130, 246, 0.08);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 14px;
  text-align: center;
}

.placeholder-text {
  font-size: 0.86rem;
  color: var(--text-main);
  font-weight: 500;
}

.placeholder-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.preview-box {
  width: 100%;
  height: 100%;
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  padding: 8px;
}

.preview-img {
  max-width: 100%;
  max-height: 160px;
  object-fit: contain;
  border-radius: var(--radius-sm);
}

.btn-clear {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 26px;
  height: 26px;
  background: rgba(0, 0, 0, 0.65);
  color: #ffffff;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.btn-clear:hover {
  background: #ef4444;
}

.hidden {
  display: none;
}
</style>
