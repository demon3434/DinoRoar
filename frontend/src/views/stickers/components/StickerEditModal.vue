<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { StickerItem } from '@/types/sticker'
import ImageUploader from '@/components/common/ImageUploader.vue'
import { showToast } from '@/utils/toast'
import { X } from 'lucide-vue-next'

const props = defineProps<{
  modelValue: boolean
  stickerData?: StickerItem | null
  categories: string[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'save', data: { name: string; category: string; price: number; sort_order: number; file: File | null }): void
}>()

const name = ref('')
const category = ref('')
const price = ref(10)
const sortOrder = ref(1)
const file = ref<File | null>(null)
const initialImageUrl = ref('')

watch(
  () => props.stickerData,
  (val) => {
    if (val) {
      name.value = val.name
      category.value = val.category
      price.value = val.price || 10
      sortOrder.value = val.sort_order || 1
      initialImageUrl.value = val.image_url
      file.value = null
    } else {
      name.value = ''
      category.value = props.categories[0] || '常用'
      price.value = 10
      sortOrder.value = 1
      initialImageUrl.value = ''
      file.value = null
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
    showToast('请输入贴纸名称', 'warning')
    return
  }
  emit('save', {
    name: name.value.trim(),
    category: category.value.trim(),
    price: price.value,
    sort_order: sortOrder.value,
    file: file.value
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
          <h3 class="modal-title">{{ stickerData ? '编辑贴纸' : '新建贴纸' }}</h3>
          <button type="button" class="btn-close" @click="handleClose">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form class="modal-body" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label class="form-label">贴纸图片</label>
            <ImageUploader
              v-model="file"
              :initial-url="initialImageUrl"
              accept="image/png,image/webp,image/gif"
            />
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">贴纸名称</label>
              <input v-model="name" type="text" class="form-input" placeholder="例如：霸王龙欢呼" required />
            </div>

            <div class="form-group">
              <label class="form-label">分类</label>
              <input v-model="category" type="text" class="form-input" placeholder="例如：恐龙日常" list="category-list" required />
              <datalist id="category-list">
                <option v-for="cat in categories" :key="cat" :value="cat" />
              </datalist>
            </div>
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label class="form-label">兑换售价 (蛋能量)</label>
              <input v-model.number="price" type="number" min="0" class="form-input" required />
            </div>

            <div class="form-group">
              <label class="form-label">排序权重</label>
              <input v-model.number="sortOrder" type="number" class="form-input" required />
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary">保存</button>
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
  max-width: 520px;
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
  border-radius: 6px;
}

.btn-close:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.1);
}

.modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.modal-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
