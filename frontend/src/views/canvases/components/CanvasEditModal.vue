<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { CanvasSet } from '@/types/canvas'
import ImageUploader from '@/components/common/ImageUploader.vue'
import { showToast } from '@/utils/toast'
import { X } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  canvasData?: CanvasSet | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'save', payload: {
    name: string
    description: string
    price: number
    sort_order: number
    previewFile: File | null
    file1_1: File | null
    file3_4: File | null
    file9_16: File | null
  }): void
}>()

const name = ref('')
const description = ref('')
const price = ref(30)
const sortOrder = ref(1)

const previewFile = ref<File | null>(null)
const initialPreviewUrl = ref('')

const file1_1 = ref<File | null>(null)
const file3_4 = ref<File | null>(null)
const file9_16 = ref<File | null>(null)

const initial1_1 = ref('')
const initial3_4 = ref('')
const initial9_16 = ref('')

watch(
  () => props.canvasData,
  (val) => {
    if (val) {
      name.value = val.name
      description.value = val.description || ''
      price.value = val.price || 30
      sortOrder.value = val.sort_order || 1
      initialPreviewUrl.value = val.preview_image_url || ''
      previewFile.value = null

      const i1_1 = val.instances?.find((i: any) => (i.ratio_name === '1:1' || i.aspect_ratio === '1:1'))
      const i3_4 = val.instances?.find((i: any) => (i.ratio_name === '3:4' || i.aspect_ratio === '3:4'))
      const i9_16 = val.instances?.find((i: any) => (i.ratio_name === '9:16' || i.aspect_ratio === '9:16'))

      initial1_1.value = i1_1?.background_image_url || ''
      initial3_4.value = i3_4?.background_image_url || ''
      initial9_16.value = i9_16?.background_image_url || ''

      file1_1.value = null
      file3_4.value = null
      file9_16.value = null
    } else {
      name.value = ''
      description.value = ''
      price.value = 30
      sortOrder.value = 1
      initialPreviewUrl.value = ''
      previewFile.value = null
      initial1_1.value = ''
      initial3_4.value = ''
      initial9_16.value = ''
      file1_1.value = null
      file3_4.value = null
      file9_16.value = null
    }
  },
  { immediate: true }
)

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
}

function handleSubmit() {
  if (!name.value.trim()) {
    showToast('请输入画布套件名称', 'warning')
    return
  }
  emit('save', {
    name: name.value.trim(),
    description: description.value.trim(),
    price: price.value,
    sort_order: sortOrder.value,
    previewFile: previewFile.value,
    file1_1: file1_1.value,
    file3_4: file3_4.value,
    file9_16: file9_16.value
  })
}

function handleKeyDown(e: KeyboardEvent) {
  if (props.modelValue && e.key === 'Escape') {
    handleClose()
  }
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      ref="modalRef"
      class="modal-backdrop"
      @mousedown="handleMouseDown"
      @click="handleClick"
    >
      <div class="modal-card animate-fade-in" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">{{ canvasData ? '编辑画布套件' : '新建画布套件' }}</h3>
          <button type="button" class="btn-close" @click="handleClose">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form class="modal-body" @submit.prevent="handleSubmit">
          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">套件名称</label>
              <input v-model="name" type="text" class="form-input" placeholder="例如：恐龙侏罗纪森林" required />
            </div>

            <div class="form-group">
              <label class="form-label">兑换售价 (蛋能量)</label>
              <input v-model.number="price" type="number" min="0" class="form-input" required />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">套件详细介绍</label>
            <input v-model="description" type="text" class="form-input" placeholder="为日记提供身临其境的远古森林氛围..." />
          </div>

          <div class="ratios-section">
            <label class="form-label">各比例背景图配置 (1:1 / 3:4 / 9:16)</label>
            <div class="ratio-grids">
              <div class="ratio-item">
                <span class="ratio-title">1:1 方形</span>
                <ImageUploader v-model="file1_1" :initial-url="initial1_1" />
              </div>
              <div class="ratio-item">
                <span class="ratio-title">3:4 经典</span>
                <ImageUploader v-model="file3_4" :initial-url="initial3_4" />
              </div>
              <div class="ratio-item">
                <span class="ratio-title">9:16 全屏</span>
                <ImageUploader v-model="file9_16" :initial-url="initial9_16" />
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary">保存套件</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: var(--modal-backdrop);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 680px;
  max-height: 90vh;
  background: var(--modal-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  padding: 20px 24px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
}

.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.ratios-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ratio-grids {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}

.ratio-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ratio-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
}

.modal-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
