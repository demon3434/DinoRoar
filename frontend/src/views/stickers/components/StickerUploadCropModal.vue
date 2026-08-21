<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

const props = withDefaults(
  defineProps<{
    open: boolean
    seriesId: number | null
    seriesName?: string
    defaultSortOrder?: number
  }>(),
  {
    defaultSortOrder: 1
  }
)

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'created'): void
}>()

const newStickerName = ref('')
const newStickerPrice = ref(10)
const newStickerSort = ref(props.defaultSortOrder || 1)
const stickerImageRef = ref<HTMLImageElement | null>(null)
const stickerCropPlaceholder = ref(true)
const fileInputRef = ref<HTMLInputElement | null>(null)
let cropperInstance: Cropper | null = null

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      newStickerSort.value = props.defaultSortOrder ?? 1
    }
  },
  { immediate: true }
)

let mouseDownOnBackdrop = false

function onBackdropMouseDown(e: MouseEvent) {
  mouseDownOnBackdrop = e.target === e.currentTarget
}

function onBackdropClick(e: MouseEvent) {
  if (mouseDownOnBackdrop && e.target === e.currentTarget) {
    handleClose()
  }
  mouseDownOnBackdrop = false
}

function handleClose() {
  newStickerName.value = ''
  newStickerPrice.value = 10
  newStickerSort.value = props.defaultSortOrder ?? 1
  stickerCropPlaceholder.value = true
  if (cropperInstance) {
    cropperInstance.destroy()
    cropperInstance = null
  }
  if (stickerImageRef.value) {
    stickerImageRef.value.src = ''
    stickerImageRef.value.style.display = 'none'
  }
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('update:open', false)
}

function initCropper(imageSrc: string) {
  stickerCropPlaceholder.value = false
  if (stickerImageRef.value) {
    stickerImageRef.value.src = imageSrc
    stickerImageRef.value.style.display = 'block'
    if (cropperInstance) {
      cropperInstance.destroy()
      cropperInstance = null
    }
    nextTick(() => {
      if (stickerImageRef.value) {
        cropperInstance = new Cropper(stickerImageRef.value, {
          aspectRatio: 1,
          viewMode: 0,
          dragMode: 'move',
          autoCropArea: 1.0,
          background: true,
          responsive: true,
          restore: false,
          checkCrossOrigin: false,
          toggleDragModeOnDblclick: false
        })
      }
    })
  }
}

function zoomIn() {
  if (cropperInstance) cropperInstance.zoom(0.1)
}

function zoomOut() {
  if (cropperInstance) cropperInstance.zoom(-0.1)
}

function resetCrop() {
  if (cropperInstance) cropperInstance.reset()
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files[0]) {
    processImageFile(target.files[0])
  }
}

function processImageFile(file: File) {
  if (!file.type.startsWith('image/')) {
    showToast('请选择有效的图片文件！', 'warning')
    return
  }
  if (!newStickerName.value) {
    const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name
    newStickerName.value = baseName.substring(0, 12)
  }
  const reader = new FileReader()
  reader.onload = (re) => {
    if (re.target?.result) {
      initCropper(re.target.result as string)
    }
  }
  reader.readAsDataURL(file)
}

function handleDragOverCrop(e: DragEvent) {
  e.preventDefault()
}

function handleDropCrop(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
    processImageFile(e.dataTransfer.files[0])
  }
}

async function triggerPasteFromClipboardBtn() {
  try {
    if (navigator.clipboard && navigator.clipboard.read) {
      const items = await navigator.clipboard.read()
      for (const item of items) {
        const imageType = item.types.find((t) => t.startsWith('image/'))
        if (imageType) {
          const blob = await item.getType(imageType)
          const file = new File([blob], 'clipboard_image.png', { type: imageType })
          processImageFile(file)
          showToast('已从剪贴板读取贴纸图片！', 'success')
          return
        }
      }
      showToast('剪贴板中未找到图片数据', 'warning')
    } else {
      showToast('由于浏览器限制，请直接在此弹窗内按 Ctrl + V 粘贴图片！', 'info')
    }
  } catch (err: any) {
    showToast('直接读取剪贴板受阻，请直接在弹窗内按键盘 Ctrl + V 粘贴！', 'info')
  }
}

function handleWindowPaste(e: ClipboardEvent) {
  if (!props.open) return
  if (e.clipboardData && e.clipboardData.items) {
    for (const item of e.clipboardData.items) {
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile()
        if (file) {
          processImageFile(file)
          showToast('已粘贴贴纸图片！', 'success')
          break
        }
      }
    }
  }
}

async function handleCreateSticker() {
  if (!props.seriesId) {
    showToast('未指定目标贴纸系列！', 'warning')
    return
  }
  if (!newStickerName.value.trim()) {
    showToast('请输入贴纸名称！', 'warning')
    return
  }
  if (!cropperInstance) {
    showToast('请先选择或粘贴贴纸图片！', 'warning')
    return
  }

  const canvas = cropperInstance.getCroppedCanvas({
    width: 256,
    height: 256,
    fillColor: 'transparent',
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high'
  })

  canvas.toBlob(async (blob) => {
    if (!blob) {
      showToast('图片裁剪生成失败，请重试！', 'error')
      return
    }

    const formData = new FormData()
    formData.append('file', blob, `${newStickerName.value.trim()}.png`)
    formData.append('series_id', String(props.seriesId))
    formData.append('name', newStickerName.value.trim())
    formData.append('exchange_price', String(newStickerPrice.value))
    formData.append('sort_order', String(newStickerSort.value))

    try {
      await apiClient.post('/api/stickers/admin/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      showToast('贴纸上传成功！', 'success')
      handleClose()
      emit('created')
    } catch (e: any) {
      const errMsg = e.response?.data?.detail || e.message || '上传贴纸失败，请重试'
      showToast(errMsg, 'error')
    }
  }, 'image/png')
}

function handleKeyDown(e: KeyboardEvent) {
  if (props.open && e.key === 'Escape') {
    handleClose()
  }
}

onMounted(() => {
  window.addEventListener('paste', handleWindowPaste)
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('paste', handleWindowPaste)
  window.removeEventListener('keydown', handleKeyDown)
  if (cropperInstance) {
    cropperInstance.destroy()
    cropperInstance = null
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="modal"
      style="display: flex; z-index: 1200;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-dialog-custom" style="max-width: 760px; width: 95%; max-height: 90vh; overflow-y: auto; padding: 22px 28px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">新增贴纸 {{ seriesName ? `(${seriesName})` : '' }}</span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <form style="display: flex; gap: 24px; flex-wrap: wrap;" @submit.prevent="handleCreateSticker">
          <!-- 左栏：文件选择与 Cropper 1:1 裁剪框 -->
          <div style="flex: 1.1; min-width: 280px; display: flex; flex-direction: column; gap: 12px;">
            <div class="form-group" style="margin: 0;">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 4px;">
                  <label class="form-label" style="margin: 0;">选择贴纸原始图片</label>
                  <span class="clipboard-tip-icon" title="由于浏览器安全策略限制，直接从剪贴板读取仅在 HTTPS/localhost 下可用。但您依然可以直接在此弹窗内通过键盘 Ctrl + V 粘贴图片！" style="cursor: help; font-size: 0.85rem; color: var(--text-muted);">❓</span>
                </div>
                <button type="button" class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.75rem; height: 26px; border-radius: 6px; margin: 0;" @click="triggerPasteFromClipboardBtn">
                  📋 剪贴板粘贴
                </button>
              </div>
              <input ref="fileInputRef" type="file" accept="image/*" class="form-control" style="margin-top: 6px;" @change="handleFileSelect" />
            </div>

            <div>
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <label class="form-label" style="margin: 0;">裁剪控制 (1:1 正方形)</label>
                <div v-if="!stickerCropPlaceholder" style="display: flex; gap: 6px;">
                  <button type="button" class="btn-tool" title="放大" @click="zoomIn">🔍+</button>
                  <button type="button" class="btn-tool" title="缩小" @click="zoomOut">🔍-</button>
                  <button type="button" class="btn-tool" title="重置" @click="resetCrop">🔄</button>
                </div>
              </div>
              <div
                class="crop-wrapper"
                style="height: 250px; border: 2px dashed var(--card-border, rgba(0, 0, 0, 0.12)); border-radius: 12px; display: flex; align-items: center; justify-content: center; background: var(--bg-surface, rgba(0, 0, 0, 0.02)); position: relative; overflow: hidden;"
                @dragover="handleDragOverCrop"
                @drop="handleDropCrop"
              >
                <div v-if="stickerCropPlaceholder" style="display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--text-muted); pointer-events: none;">
                  <span style="font-size: 2.2rem; opacity: 0.5;">🎨</span>
                  <span style="font-size: 0.8rem; font-weight: 500;">拖拽/粘贴图片或选择本地文件</span>
                </div>
                <img ref="stickerImageRef" src="" style="display: none; max-width: 100%;" />
              </div>
              <div v-if="!stickerCropPlaceholder" style="font-size: 0.72rem; color: var(--text-muted); margin-top: 4px; text-align: center;">
                💡 滚轮或按键可缩放图像，拖拽可移动位置，确保完整画面纳于选框中
              </div>
            </div>
          </div>

          <!-- 右栏：贴纸属性表单 -->
          <div style="flex: 1; min-width: 260px; display: flex; flex-direction: column; gap: 14px; justify-content: space-between;">
            <div style="display: flex; flex-direction: column; gap: 14px;">
              <div class="form-group" style="margin: 0;">
                <label class="form-label">贴纸名称</label>
                <input v-model="newStickerName" type="text" class="form-control" placeholder="例如：水果恐龙" maxlength="12" required />
              </div>

              <div class="form-group" style="margin: 0;">
                <label class="form-label">所需蛋能量</label>
                <input v-model="newStickerPrice" type="number" class="form-control" min="0" required />
              </div>

              <div class="form-group" style="margin: 0;">
                <label class="form-label">内部排序</label>
                <input v-model="newStickerSort" type="number" class="form-control" min="0" required />
              </div>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 15px;">
              <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
              <button type="submit" class="btn btn-primary-purple">确定上传</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.crop-wrapper {
  width: 100%;
  box-sizing: border-box;
}

.btn-tool {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-weight: 600;
  background: var(--bg-surface, #f3f4f6);
  border: 1px solid var(--card-border, #e5e7eb);
  border-radius: 6px;
  color: var(--text-main, #374151);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-tool:hover {
  background: var(--accent-purple-light, rgba(124, 58, 237, 0.1));
  color: var(--accent-purple, #7c3aed);
  border-color: var(--accent-purple, #7c3aed);
}
</style>
