<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
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
  seriesId: number
  set?: CanvasSet | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'saved'): void
}>()

const setName = ref('')
const setDesc = ref('')
const setPrice = ref(50)
const setSortOrder = ref(1)

watch(
  () => props.set,
  (val) => {
    if (val) {
      setName.value = val.name
      setDesc.value = val.description || ''
      setPrice.value = val.exchange_price || 50
      setSortOrder.value = val.sort_order || 1
    } else {
      setName.value = ''
      setDesc.value = ''
      setPrice.value = 50
      setSortOrder.value = 1
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
  emit('update:open', false)
}

async function handleSubmit() {
  if (!setName.value.trim()) {
    showToast('请输入画布套件名称！', 'warning')
    return
  }

  try {
    if (props.set) {
      await apiClient.put(`/api/canvases/admin/sets/${props.set.id}`, {
        name: setName.value.trim(),
        description: setDesc.value.trim(),
        exchange_price: Number(setPrice.value),
        sort_order: Number(setSortOrder.value)
      })
      showToast('画布套件已更新！', 'success')
    } else {
      await apiClient.post(`/api/canvases/admin/series/${props.seriesId}/sets`, {
        series_id: Number(props.seriesId),
        name: setName.value.trim(),
        description: setDesc.value.trim(),
        exchange_price: Number(setPrice.value),
        sort_order: Number(setSortOrder.value)
      })
      showToast('画布套件创建成功！', 'success')
    }
    handleClose()
    emit('saved')
  } catch (e: any) {
    showToast(e.response?.data?.detail || '保存画布套件失败', 'error')
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
      style="display: flex; z-index: 1200;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-dialog-custom" style="max-width: 460px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            {{ set ? '编辑画布套件' : '新建画布套件' }}
          </span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <form style="display: flex; flex-direction: column; gap: 14px;" @submit.prevent="handleSubmit">
          <div class="form-group" style="margin: 0;">
            <label class="form-label">套件名称</label>
            <input v-model="setName" type="text" class="form-control" placeholder="例如：恐龙绿洲" maxlength="15" required />
          </div>

          <div class="form-group" style="margin: 0;">
            <label class="form-label">文案描述 (选填)</label>
            <input v-model="setDesc" type="text" class="form-control" placeholder="例如：远古绿野与清凉湖泊" maxlength="30" />
          </div>

          <div class="form-group" style="margin: 0;">
            <label class="form-label">所需蛋能量</label>
            <input v-model="setPrice" type="number" class="form-control" min="0" required />
          </div>

          <div class="form-group" style="margin: 0;">
            <label class="form-label">排序顺序</label>
            <input v-model="setSortOrder" type="number" class="form-control" value="1" />
          </div>

          <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
            <button type="button" class="btn btn-secondary" @click="handleClose">取消</button>
            <button type="submit" class="btn btn-primary-purple">确定保存</button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
