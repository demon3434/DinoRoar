<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

const props = withDefaults(
  defineProps<{
    open: boolean
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

const newSeriesName = ref('')
const newSeriesSort = ref(props.defaultSortOrder || 1)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      newSeriesName.value = ''
      newSeriesSort.value = props.defaultSortOrder ?? 1
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
  newSeriesName.value = ''
  newSeriesSort.value = props.defaultSortOrder ?? 1
  emit('update:open', false)
}

async function handleCreateSeries() {
  if (!newSeriesName.value.trim()) {
    showToast('请输入系列名称！', 'warning')
    return
  }
  try {
    await apiClient.post('/api/canvases/admin/series', {
      name: newSeriesName.value.trim(),
      sort_order: Number(newSeriesSort.value) || 1
    })
    showToast('画布系列创建成功！', 'success')
    handleClose()
    emit('created')
  } catch (e: any) {
    showToast(e.response?.data?.detail || '创建系列失败', 'error')
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (props.open && e.key === 'Escape') {
    handleClose()
  }
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="modal"
      style="display: flex;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-dialog-custom" style="max-width: 420px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">新建画布系列</span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>
        <form style="display: flex; flex-direction: column; gap: 16px;" @submit.prevent="handleCreateSeries">
          <div class="form-group" style="margin: 0;">
            <label class="form-label">系列名称</label>
            <input v-model="newSeriesName" type="text" class="form-control" placeholder="例如：远古白垩纪、魔法森林" required />
          </div>
          <div class="form-group" style="margin: 0;">
            <label class="form-label">排序顺序</label>
            <input v-model="newSeriesSort" type="number" class="form-control" />
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
            <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary-purple">确定创建</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
