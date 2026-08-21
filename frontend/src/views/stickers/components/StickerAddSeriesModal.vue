<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    defaultSortOrder?: number
  }>(),
  {
    defaultSortOrder: 1
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'confirm', data: { name: string; sort_order: number }): void
}>()

const name = ref('')
const sortOrder = ref(props.defaultSortOrder || 1)

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
  emit('update:modelValue', false)
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      name.value = ''
      sortOrder.value = props.defaultSortOrder ?? 1
    }
  }
)

function handleSubmit() {
  if (!name.value.trim()) return
  emit('confirm', { name: name.value.trim(), sort_order: Number(sortOrder.value) || 1 })
  handleClose()
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
      class="modal"
      style="display: flex; z-index: 1000;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick($event, handleClose)"
    >
      <div class="modal-dialog-custom" style="max-width: 420px;" @click.stop>
        <div class="modal-header">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">新建贴纸系列</span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>
        <form style="display: flex; flex-direction: column; gap: 16px;" @submit.prevent="handleSubmit">
          <div class="form-group" style="margin: 0;">
            <label class="form-label">系列名称</label>
            <input v-model="name" type="text" class="form-control" placeholder="例如：太空柯基、水果派对" required />
          </div>
          <div class="form-group" style="margin: 0;">
            <label class="form-label">排序顺序</label>
            <input v-model="sortOrder" type="number" class="form-control" />
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
