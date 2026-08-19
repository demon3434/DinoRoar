<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import CanvasLightboxModal from './CanvasLightboxModal.vue'
import CanvasSetDetailCard from './CanvasSetDetailCard.vue'

interface CanvasInstance {
  id: number
  set_id: number
  aspect_ratio: string
  image_url: string
  is_deleted?: boolean
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

interface CanvasSeries {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  sets: CanvasSet[]
}

const props = defineProps<{
  open: boolean
  series: CanvasSeries | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'open-add-set'): void
  (e: 'open-edit-set', set: CanvasSet): void
  (e: 'open-upload-instance', set: CanvasSet, ratio: string): void
  (e: 'toggle-set-active', ev: Event, set: CanvasSet): void
  (e: 'delete-set', ev: Event, set: CanvasSet): void
  (e: 'reorder-success'): void
  (e: 'batch-delete-success'): void
}>()

// 批量删除模式状态
const isBatchDeleteMode = ref(false)
const selectedDeleteSetIds = ref<number[]>([])
const isBatchConfirmModalOpen = ref(false)

// 弹窗关闭时自动重置批量删除状态
watch(
  () => props.open,
  (isOpen) => {
    if (!isOpen) {
      isBatchDeleteMode.value = false
      selectedDeleteSetIds.value = []
      isBatchConfirmModalOpen.value = false
    }
  }
)

// 计算当前系列中可被删除的套件列表（排除系统预设底图 3001）
const deletableSets = computed(() => {
  if (!props.series?.sets) return []
  return props.series.sets.filter((s) => s.id !== 3001)
})

const isAllDeletableSelected = computed(() => {
  return (
    deletableSets.value.length > 0 &&
    selectedDeleteSetIds.value.length === deletableSets.value.length
  )
})

// 单项勾选/取消勾选
function toggleDeleteSetSelect(setId: number) {
  if (setId === 3001) return
  if (selectedDeleteSetIds.value.includes(setId)) {
    selectedDeleteSetIds.value = selectedDeleteSetIds.value.filter((id) => id !== setId)
  } else {
    selectedDeleteSetIds.value.push(setId)
  }
}

// 批量全选/全不选
function toggleSelectAllDetailSets(e: Event) {
  const checked = (e.target as HTMLInputElement).checked
  if (checked) {
    selectedDeleteSetIds.value = deletableSets.value.map((s) => s.id)
  } else {
    selectedDeleteSetIds.value = []
  }
}

// 触发批量删除二次确认
function promptBatchDelete() {
  if (selectedDeleteSetIds.value.length === 0) {
    showToast('请先勾选需要批量删除的画布套件！', 'warning')
    return
  }
  isBatchConfirmModalOpen.value = true
}

// 确认提交批量删除请求
async function handleConfirmBatchDeleteSubmit() {
  if (selectedDeleteSetIds.value.length === 0) return
  try {
    const res: any = await apiClient.post('/api/canvases/admin/sets/batch-delete', {
      set_ids: selectedDeleteSetIds.value
    })
    showToast(res?.message || '批量删除画布套件成功！', 'success')
    isBatchDeleteMode.value = false
    selectedDeleteSetIds.value = []
    isBatchConfirmModalOpen.value = false
    emit('batch-delete-success')
  } catch (err: any) {
    showToast(err.response?.data?.detail || err.message || '批量删除失败', 'error')
  }
}

// 每个套件选中的当前宽高比 (setId -> ratio)
const currentActiveRatios = ref<Record<number, string>>({})

// Lightbox 全屏大图查看状态
const isLightboxOpen = ref(false)
const lightboxImageUrl = ref('')
const lightboxTitle = ref('')

function handleCardToggleActive(ev: Event, set: CanvasSet) {
  emit('toggle-set-active', ev, set)
}

function handleCardDelete(ev: Event, set: CanvasSet) {
  emit('delete-set', ev, set)
}

// 拖拽排序状态
let draggedSet: CanvasSet | null = null

function handleSetDragStart(e: DragEvent, set: CanvasSet) {
  if (isBatchDeleteMode.value) return
  draggedSet = set
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(set.id))
  }
}

function handleSetDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

function handleSetDragEnter(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.set-detail-card')
  if (target) target.classList.add('over')
}

function handleSetDragLeave(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.set-detail-card')
  if (target) target.classList.remove('over')
}

async function handleSetDrop(e: DragEvent, targetSet: CanvasSet) {
  e.preventDefault()
  const target = (e.target as HTMLElement).closest('.set-detail-card')
  if (target) target.classList.remove('over')

  if (!draggedSet || draggedSet.id === targetSet.id || !props.series) return

  const list = [...props.series.sets]
  const fromIdx = list.findIndex((s) => s.id === draggedSet!.id)
  const toIdx = list.findIndex((s) => s.id === targetSet.id)

  if (fromIdx !== -1 && toIdx !== -1) {
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    props.series.sets = list

    const orderedIds = list.map((s) => s.id)
    try {
      await apiClient.put('/api/canvases/admin/sets/sort', {
        series_id: props.series.id,
        ordered_ids: orderedIds
      })
      showToast('画布排序更新成功！', 'success')
      emit('reorder-success')
    } catch (err: any) {
      showToast('更新画布排序失败', 'error')
    }
  }
  draggedSet = null
}

function handleSetDragEnd() {
  document.querySelectorAll('.set-detail-card.over').forEach((el) => el.classList.remove('over'))
  draggedSet = null
}

function getActiveRatio(setId: number) {
  return currentActiveRatios.value[setId] || '16:9'
}

function selectRatio(setId: number, ratio: string) {
  currentActiveRatios.value[setId] = ratio
}

function openLightbox(imageUrl: string, title: string) {
  lightboxImageUrl.value = imageUrl
  lightboxTitle.value = title
  isLightboxOpen.value = true
}

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
  emit('update:open', false)
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (isLightboxOpen.value) {
      isLightboxOpen.value = false
    } else if (isBatchConfirmModalOpen.value) {
      isBatchConfirmModalOpen.value = false
    } else if (isBatchDeleteMode.value) {
      isBatchDeleteMode.value = false
      selectedDeleteSetIds.value = []
    } else if (props.open) {
      handleClose()
    }
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
      v-if="open"
      class="modal"
      style="display: flex; z-index: 1000;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick($event, handleClose)"
    >
      <div
        class="modal-dialog-custom"
        style="max-width: 1180px; width: 95%; max-height: 90vh; height: 86vh; display: flex; flex-direction: column; overflow: hidden; padding: 18px 24px; box-sizing: border-box;"
        @click.stop
      >
        <!-- 弹窗 Header 导航与操作区 -->
        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-shrink: 0; margin-bottom: 8px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border);">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            🖼️ 「{{ series?.name || '未知系列' }}」画布详情 (共 {{ series?.sets?.length || 0 }} 套)
          </span>

          <div style="display: flex; gap: 12px; align-items: center;">
            <!-- 平时状态按钮组 -->
            <div v-if="!isBatchDeleteMode" style="display: flex; gap: 10px; align-items: center;">
              <button
                type="button"
                class="btn-outline-purple"
                style="margin: 0; font-size: 0.8rem; padding: 4px 12px; height: 32px;"
                :disabled="!series?.sets || series.sets.length === 0"
                @click="isBatchDeleteMode = true"
              >
                🗑️ 批量删除
              </button>
              <button
                type="button"
                class="btn btn-primary-purple"
                style="margin: 0; font-size: 0.8rem; padding: 4px 14px; height: 32px; font-weight: 700;"
                @click="emit('open-add-set')"
              >
                + 新增画布
              </button>
            </div>

            <!-- 批量删除模式按钮组 -->
            <div v-else style="display: flex; gap: 10px; align-items: center;">
              <label style="font-size: 0.8rem; cursor: pointer; color: #ef4444; font-weight: 800; display: inline-flex; align-items: center; gap: 4px;">
                <input
                  type="checkbox"
                  :checked="isAllDeletableSelected"
                  style="accent-color: #ef4444; width: 15px; height: 15px; cursor: pointer;"
                  @change="toggleSelectAllDetailSets"
                /> 全选
              </label>
              <button
                type="button"
                class="btn"
                style="margin: 0; background: #ef4444; border: 1px solid #ef4444; color: #fff; font-size: 0.78rem; padding: 4px 12px; height: 32px; font-weight: 800; border-radius: 8px;"
                :disabled="selectedDeleteSetIds.length === 0"
                @click="promptBatchDelete"
              >
                🔥 确认删除 ({{ selectedDeleteSetIds.length }})
              </button>
              <button
                type="button"
                class="btn-outline-purple"
                style="margin: 0; font-size: 0.78rem; padding: 4px 12px; height: 32px;"
                @click="isBatchDeleteMode = false; selectedDeleteSetIds = []"
              >
                退出批量删除
              </button>
            </div>

            <!-- 右上角红叉关闭按钮 -->
            <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
          </div>
        </div>

        <!-- 卡片平铺网格流 -->
        <div style="flex: 1; overflow-y: auto; min-height: 0; margin-top: 4px; padding-right: 4px;">
          <div v-if="!series?.sets || series.sets.length === 0" style="text-align: center; padding: 80px 20px; color: var(--text-muted);">
            <div style="font-size: 2.5rem; margin-bottom: 8px; opacity: 0.6;">🖼️</div>
            该系列下暂无画布套件，点击右上角「+ 新增画布」添加
          </div>

          <div v-else class="sets-list-grid">
            <CanvasSetDetailCard
              v-for="set in series.sets"
              :key="set.id"
              :set="set"
              :active-ratio="getActiveRatio(set.id)"
              :is-batch-delete-mode="isBatchDeleteMode"
              :is-selected-for-delete="selectedDeleteSetIds.includes(set.id)"
              @select-ratio="selectRatio(set.id, $event)"
              @toggle-delete="toggleDeleteSetSelect(set.id)"
              @open-lightbox="openLightbox"
              @open-edit="emit('open-edit-set', $event)"
              @open-upload="(s, r) => emit('open-upload-instance', s, r)"
              @toggle-active="handleCardToggleActive"
              @delete="handleCardDelete"
              @dragstart="handleSetDragStart($event, set)"
              @dragover="handleSetDragOver"
              @dragenter="handleSetDragEnter"
              @dragleave="handleSetDragLeave"
              @drop="handleSetDrop($event, set)"
              @dragend="handleSetDragEnd"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 批量删除确认弹层 -->
    <ConfirmModal
      v-model="isBatchConfirmModalOpen"
      title="批量删除画布套件确认"
      :message="`确定要批量删除选中的 ${selectedDeleteSetIds.length} 套画布套件吗？其下属所有尺寸裁剪底图将一并软删除！`"
      confirm-text="确认删除"
      type="danger"
      @confirm="handleConfirmBatchDeleteSubmit"
    />

    <!-- Lightbox 原图全屏预览模态框 -->
    <CanvasLightboxModal
      v-model="isLightboxOpen"
      :image-url="lightboxImageUrl"
      :title="lightboxTitle"
    />
  </Teleport>
</template>

<style scoped>
.sets-list-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  padding: 6px 8px;
}
</style>
