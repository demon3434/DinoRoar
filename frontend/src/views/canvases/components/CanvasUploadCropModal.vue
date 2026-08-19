<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

interface CanvasInstance {
  id: number
  set_id: number
  aspect_ratio: string
  image_url: string
}

interface CanvasSet {
  id: number
  series_id: number
  name: string
  description?: string
  exchange_price: number
  sort_order: number
  is_active: boolean
  instances: CanvasInstance[]
}

const props = defineProps<{
  open: boolean
  targetSet: CanvasSet | null
  initialRatio?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'uploaded'): void
}>()

const ratioMap: Record<string, number> = {
  '16:9': 16 / 9,
  '4:3': 4 / 3,
  '1:1': 1.0,
  '2:1': 2.0
}

const selectedRatio = ref('16:9')
const canvasCropperImgRef = ref<HTMLImageElement | null>(null)
const cropperPlaceholder = ref(true)
const canvasFileInputRef = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
let cropperInstance: Cropper | null = null

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      selectedRatio.value = props.initialRatio && ratioMap[props.initialRatio] ? props.initialRatio : '16:9'
      cropperPlaceholder.value = true
      isUploading.value = false
    } else {
      handleClose()
    }
  }
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
  cropperPlaceholder.value = true
  isUploading.value = false
  if (cropperInstance) {
    cropperInstance.destroy()
    cropperInstance = null
  }
  if (canvasCropperImgRef.value) {
    canvasCropperImgRef.value.src = ''
    canvasCropperImgRef.value.style.display = 'none'
  }
  if (canvasFileInputRef.value) {
    canvasFileInputRef.value.value = ''
  }
  emit('update:open', false)
}

function onRatioChange(ratio: string) {
  selectedRatio.value = ratio
  if (cropperInstance) {
    const aspectVal = ratioMap[ratio] || 16 / 9
    cropperInstance.setAspectRatio(aspectVal)
  }
}

function initCropper(imageSrc: string) {
  cropperPlaceholder.value = false
  if (canvasCropperImgRef.value) {
    canvasCropperImgRef.value.src = imageSrc
    canvasCropperImgRef.value.style.display = 'block'
    if (cropperInstance) {
      cropperInstance.destroy()
      cropperInstance = null
    }
    nextTick(() => {
      if (canvasCropperImgRef.value) {
        const aspectVal = ratioMap[selectedRatio.value] || 16 / 9
        cropperInstance = new Cropper(canvasCropperImgRef.value, {
          aspectRatio: aspectVal,
          viewMode: 0,
          dragMode: 'move',
          autoCropArea: 1,
          restore: false,
          guides: true,
          center: true,
          highlight: false,
          cropBoxMovable: true,
          cropBoxResizable: true,
          toggleDragModeOnDblclick: false
        })
      }
    })
  }
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
          const file = new File([blob], 'clipboard_canvas.png', { type: imageType })
          processImageFile(file)
          showToast('已从剪贴板读取底图！', 'success')
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
          showToast('已粘贴底图！', 'success')
          break
        }
      }
    }
  }
}

async function handleUploadCroppedCanvas() {
  if (!props.targetSet) return
  if (!cropperInstance) {
    showToast('请先选择并裁剪图片', 'info')
    return
  }

  const r_val = ratioMap[selectedRatio.value] || 16 / 9
  const targetWidth = 1440
  const targetHeight = Math.round(targetWidth / r_val)

  const canvas = cropperInstance.getCroppedCanvas({
    width: targetWidth,
    height: targetHeight,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high'
  })

  isUploading.value = true

  canvas.toBlob(async (blob) => {
    if (!blob) {
      showToast('裁剪处理失败', 'error')
      isUploading.value = false
      return
    }

    const formData = new FormData()
    formData.append('set_id', String(props.targetSet!.id))
    formData.append('canvas_set_id', String(props.targetSet!.id))
    formData.append('aspect_ratio', selectedRatio.value)
    formData.append('file', blob, `canvas_${props.targetSet!.id}_${selectedRatio.value.replace(':', '_')}.png`)

    try {
      await apiClient.post('/api/canvases/admin/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      showToast('画布图片上传成功！', 'success')
      handleClose()
      emit('uploaded')
    } catch (e: any) {
      const errMsg = e.response?.data?.detail || e.message || '画布底图上传失败'
      showToast(`❌ 上传失败: ${errMsg}`, 'error')
    } finally {
      isUploading.value = false
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
      v-if="open && targetSet"
      class="modal admin-modal"
      style="display: flex; z-index: 1200;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div
        class="modal-content modal-dialog-custom"
        style="width: 860px; max-width: 95%; max-height: 90vh; overflow-y: auto; padding: 22px 28px;"
        @click.stop
      >
        <div class="modal-header">
          <h3 class="modal-title" style="font-weight: 800; font-size: 1.15rem; color: var(--text-main); margin: 0;">
            上传并裁剪画布图片
          </h3>
          <span class="modal-close-icon" title="关闭" style="cursor: pointer; font-size: 1.5rem;" @click="handleClose">✕</span>
        </div>

        <div style="display: flex; gap: 25px; align-items: stretch; margin-top: 10px; flex-wrap: wrap;">
          <!-- 左侧栏：文件选择与裁剪器 -->
          <div style="flex: 1.2; min-width: 320px; display: flex; flex-direction: column; gap: 12px; text-align: left;">
            <div class="form-group" style="margin: 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <label style="font-weight: 700; color: var(--text-muted); font-size: 0.82rem; margin: 0;">选择本地底图</label>
                  <span
                    class="clipboard-tip-icon"
                    title="由于浏览器安全策略限制，直接点击按钮读取剪贴板仅在 HTTPS 或 localhost 环境下可用。但您依然可以直接在此弹窗内通过键盘 Ctrl + V 粘贴图片！"
                    style="cursor: help; font-size: 0.85rem; color: var(--text-muted);"
                  >❓</span>
                </div>
                <button
                  class="btn-outline-purple"
                  style="padding: 2px 10px; font-size: 0.72rem; height: 26px; border-radius: 6px; margin: 0; border: 1px solid rgba(139, 92, 246, 0.4); cursor: pointer;"
                  type="button"
                  @click="triggerPasteFromClipboardBtn"
                >
                  📋 剪贴板粘贴
                </button>
              </div>
              <input
                ref="canvasFileInputRef"
                type="file"
                accept="image/*"
                class="form-control-input"
                style="padding-top: 8px; width: 100%; box-sizing: border-box;"
                @change="handleFileSelect"
              />
            </div>
            <div
              class="cropper-wrapper"
              style="height: 320px; border: 2px dashed var(--card-border, rgba(255,255,255,0.08)); border-radius: 12px; display: flex; align-items: center; justify-content: center; background: var(--bg-surface, rgba(255,255,255,0.01)); position: relative; overflow: hidden; margin-top: 10px;"
              @dragover="handleDragOverCrop"
              @drop="handleDropCrop"
            >
              <!-- 占位元素 -->
              <div
                v-if="cropperPlaceholder"
                style="display: flex; flex-direction: column; align-items: center; gap: 10px; color: var(--text-muted); text-align: center; pointer-events: none;"
              >
                <span style="font-size: 2.2rem; opacity: 0.5;">🖼️</span>
                <span style="font-size: 0.8rem; font-weight: 500;">拖拽/粘贴图片或点击上方选择文件</span>
              </div>
              <img ref="canvasCropperImgRef" src="" style="display: none; max-height: 100%; max-width: 100%;" />
            </div>
          </div>

          <!-- 右侧栏：控制与上传 -->
          <div style="flex: 0.8; min-width: 260px; display: flex; flex-direction: column; gap: 15px; justify-content: space-between; text-align: left;">
            <div>
              <div class="form-group">
                <label style="font-weight: 700; color: var(--text-muted); font-size: 0.82rem; margin-bottom: 6px; display: block;">选择目标宽高比</label>
                <select
                  v-model="selectedRatio"
                  class="form-control-input"
                  style="padding: 0 8px; width: 100%; height: 38px; box-sizing: border-box;"
                  @change="onRatioChange(selectedRatio)"
                >
                  <option value="16:9">16:9 比例 (横向宽屏)</option>
                  <option value="4:3">4:3 比例 (小横屏)</option>
                  <option value="1:1">1:1 比例 (正方形)</option>
                  <option value="2:1">2:1 比例 (超宽横幅)</option>
                </select>
              </div>
              <div style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; margin-top: 10px; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px solid var(--card-border);">
                💡 <b>提示说明：</b><br />
                您可以在左侧框内拖动/缩放选框进行裁剪。图片将统一物理重采样为宽度 <b>1440px</b> 格式化存储，杜绝拉伸变形。
              </div>
            </div>

            <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
              <button type="button" class="btn btn-secondary" style="padding: 8px 16px; font-size: 0.82rem;" @click="handleClose">取消</button>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="cropperPlaceholder || isUploading"
                style="padding: 8px 20px; font-size: 0.82rem;"
                @click="handleUploadCroppedCanvas"
              >
                {{ isUploading ? '正在上传...' : '裁剪并上传' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--card-border);
}

.cropper-wrapper {
  width: 100%;
  box-sizing: border-box;
}

.form-control-input {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  border-radius: 10px;
  color: var(--text-main);
  padding: 0 12px;
  font-size: 0.85rem;
  outline: none;
  transition: all 0.2s;
}

.form-control-input:focus {
  border-color: #8b5cf6;
}

.btn-primary {
  background: linear-gradient(135deg, #8b5cf6, #a78bfa);
  border: none;
  color: white;
  padding: 8px 20px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(139, 92, 246, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
  color: var(--text-main);
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.modal-close-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: #ef4444;
  font-size: 1.1rem;
  font-weight: 800;
  transition: all 0.2s ease;
}

.modal-close-icon:hover {
  background: #ef4444 !important;
  border-color: #ef4444 !important;
  color: #ffffff !important;
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.35);
}
</style>
