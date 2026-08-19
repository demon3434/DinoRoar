<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

interface StickerItem {
  id: number
  name: string
  image_url: string
  exchange_price?: number
  sort_order?: number
  is_active?: boolean
}

interface StickerSeries {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  stickers: StickerItem[]
}

const props = defineProps<{
  open: boolean
  series: StickerSeries | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'open-add-sticker'): void
  (e: 'prompt-delete-single', sticker: StickerItem): void
  (e: 'reorder-success'): void
  (e: 'batch-delete-success'): void
}>()

const isBatchDeleteMode = ref(false)
const selectedDeleteStickerIds = ref<number[]>([])
const isBatchConfirmModalOpen = ref(false)
let draggedSticker: StickerItem | null = null

watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      isBatchDeleteMode.value = false
      selectedDeleteStickerIds.value = []
      isBatchConfirmModalOpen.value = false
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
  emit('update:open', false)
}

function toggleDeleteStickerSelect(stkId: number) {
  if (selectedDeleteStickerIds.value.includes(stkId)) {
    selectedDeleteStickerIds.value = selectedDeleteStickerIds.value.filter((id) => id !== stkId)
  } else {
    selectedDeleteStickerIds.value.push(stkId)
  }
}

function toggleSelectAllDetailStickers(e: Event) {
  const checked = (e.target as HTMLInputElement).checked
  if (checked && props.series?.stickers) {
    selectedDeleteStickerIds.value = props.series.stickers.map((s) => s.id)
  } else {
    selectedDeleteStickerIds.value = []
  }
}

function promptBatchDeleteStickers() {
  if (selectedDeleteStickerIds.value.length === 0) {
    showToast('请先勾选需要批量删除的贴纸！', 'warning')
    return
  }
  isBatchConfirmModalOpen.value = true
}

async function handleConfirmBatchDeleteStickersSubmit() {
  if (selectedDeleteStickerIds.value.length === 0) return
  try {
    const res: any = await apiClient.post('/api/stickers/admin/batch-delete', {
      sticker_ids: selectedDeleteStickerIds.value
    })
    showToast(res?.message || '批量删除贴纸成功！', 'success')
    isBatchConfirmModalOpen.value = false
    isBatchDeleteMode.value = false
    selectedDeleteStickerIds.value = []
    emit('batch-delete-success')
  } catch (err: any) {
    showToast(err.response?.data?.detail || '批量删除失败', 'error')
  }
}

// 拖拽排序
function handleStickerDragStart(e: DragEvent, sticker: StickerItem) {
  if (isBatchDeleteMode.value) return
  draggedSticker = sticker
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(sticker.id))
  }
}

function handleStickerDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

function handleStickerDragEnter(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.sticker-item')
  if (target) target.classList.add('over')
}

function handleStickerDragLeave(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.sticker-item')
  if (target) target.classList.remove('over')
}

async function handleStickerDrop(e: DragEvent, targetSticker: StickerItem) {
  e.preventDefault()
  const target = (e.target as HTMLElement).closest('.sticker-item')
  if (target) target.classList.remove('over')

  if (!draggedSticker || !props.series || draggedSticker.id === targetSticker.id) return

  const list = [...props.series.stickers]
  const fromIdx = list.findIndex((s) => s.id === draggedSticker!.id)
  const toIdx = list.findIndex((s) => s.id === targetSticker.id)

  if (fromIdx !== -1 && toIdx !== -1) {
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    props.series.stickers = list

    const orderedIds = list.map((s) => s.id)
    try {
      await apiClient.post(`/api/stickers/admin/series/${props.series.id}/stickers/reorder`, {
        ordered_ids: orderedIds
      })
      showToast('贴纸排序更新成功！', 'success')
      emit('reorder-success')
    } catch (err) {
      showToast('贴纸排序更新失败', 'error')
    }
  }
  draggedSticker = null
}

function handleStickerDragEnd() {
  draggedSticker = null
  const items = document.querySelectorAll('.sticker-item')
  items.forEach((it) => it.classList.remove('over'))
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (isBatchConfirmModalOpen.value) {
      isBatchConfirmModalOpen.value = false
    } else if (isBatchDeleteMode.value) {
      isBatchDeleteMode.value = false
      selectedDeleteStickerIds.value = []
    } else if (props.open) {
      handleClose()
    }
  }
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open && series"
      class="modal"
      style="display: flex; z-index: 1000;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-content" style="max-width: 960px; width: 95%; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; padding: 18px 24px; box-sizing: border-box;" @click.stop>
        <!-- 弹窗 Header (1:1 严格对齐 194) -->
        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-shrink: 0; margin-bottom: 8px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border);">
          <span style="font-weight: 800; font-size: 1.15rem;">📁 文件夹贴纸详情 ({{ series.name }})</span>

          <div style="display: flex; gap: 10px; align-items: center;">
            <!-- 详情平时操作组 -->
            <div v-if="!isBatchDeleteMode" style="display: flex; gap: 10px; align-items: center;">
              <button class="btn-outline-purple" style="margin: 0; font-size: 0.8rem; padding: 4px 12px; height: 32px;" @click="isBatchDeleteMode = true">
                🗑 批量删除
              </button>
              <button class="btn btn-primary-purple" style="margin: 0; font-size: 0.8rem; padding: 4px 12px; height: 32px;" @click="emit('open-add-sticker')">
                + 新增贴纸
              </button>
            </div>
            <!-- 详情批量删除操作组 -->
            <div v-else style="display: flex; gap: 10px; align-items: center;">
              <label style="font-size: 0.8rem; cursor: pointer; color: #ef4444; font-weight: 800; display: inline-flex; align-items: center; gap: 4px;">
                <input type="checkbox" style="accent-color: #ef4444; width: 15px; height: 15px; cursor: pointer;" @change="toggleSelectAllDetailStickers" /> 全选
              </label>
              <button class="btn" style="margin: 0; background: #ef4444; border-color: #ef4444; color: #fff; font-size: 0.8rem; padding: 4px 12px; height: 32px; font-weight: 800;" @click="promptBatchDeleteStickers">
                🔥 确认删除 ({{ selectedDeleteStickerIds.length }})
              </button>
              <button class="logout-btn" style="margin: 0; font-size: 0.8rem; padding: 4px 12px; height: 32px;" @click="isBatchDeleteMode = false; selectedDeleteStickerIds = []">
                退出批量删除
              </button>
            </div>
            <!-- 关闭按钮 -->
            <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
          </div>
        </div>

        <!-- 贴纸网格列表 (支持 HTML5 拖拽调整顺序) -->
        <div class="sticker-list-grid" style="flex: 1; overflow-y: auto; min-height: 0; margin-top: 6px;">
          <div
            v-for="stk in series.stickers"
            :key="stk.id"
            class="sticker-item"
            :class="{
              'batch-delete-active': isBatchDeleteMode,
              'batch-delete-selected': isBatchDeleteMode && selectedDeleteStickerIds.includes(stk.id)
            }"
            :draggable="!isBatchDeleteMode"
            @click="isBatchDeleteMode ? toggleDeleteStickerSelect(stk.id) : null"
            @dragstart="handleStickerDragStart($event, stk)"
            @dragover="handleStickerDragOver"
            @dragenter="handleStickerDragEnter"
            @dragleave="handleStickerDragLeave"
            @drop="handleStickerDrop($event, stk)"
            @dragend="handleStickerDragEnd"
          >
            <input
              v-if="isBatchDeleteMode"
              type="checkbox"
              class="sticker-batch-checkbox"
              :checked="selectedDeleteStickerIds.includes(stk.id)"
              @click.stop
              @change="toggleDeleteStickerSelect(stk.id)"
            />
            <span
              v-else
              class="sticker-delete-trigger"
              title="删除贴纸"
              @click.stop="emit('prompt-delete-single', stk)"
            >✕</span>

            <img :src="stk.image_url" :alt="stk.name" loading="lazy" />
            <span class="sticker-item-name" :title="stk.name">{{ stk.name }}</span>
            <span class="sticker-item-price">🥚 {{ stk.exchange_price || 10 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量删除二次确认弹层 -->
    <ConfirmModal
      v-model="isBatchConfirmModalOpen"
      title="批量删除贴纸确认"
      :message="`确定要批量删除选中的 ${selectedDeleteStickerIds.length} 张贴纸吗？删除后将彻底从该系列中移除！`"
      confirm-text="确认删除"
      type="danger"
      @confirm="handleConfirmBatchDeleteStickersSubmit"
    />
  </Teleport>
</template>

<style scoped>
.sticker-item.over {
  border: 2px dashed #8b5cf6 !important;
  transform: scale(1.03);
}
</style>
