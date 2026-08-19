<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

interface ImportStickerItem {
  name: string
  image_b64: string
}

interface ImportSeriesItem {
  series_name: string
  sticker_count: number
  is_name_conflict: boolean
  stickers: ImportStickerItem[]
}

const props = defineProps<{
  open: boolean
  zipFileName: string
  tempToken: string
  seriesList: ImportSeriesItem[]
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'import-success'): void
  (e: 'close'): void
}>()

const selectedImportSeriesNames = ref<string[]>([])
const importConflictResolution = ref<'rename' | 'merge' | 'skip'>('rename')
const isImporting = ref(false)

watch(
  () => props.seriesList,
  (list) => {
    selectedImportSeriesNames.value = list.map((s) => s.series_name)
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

function toggleImportSeriesSelect(name: string) {
  if (selectedImportSeriesNames.value.includes(name)) {
    selectedImportSeriesNames.value = selectedImportSeriesNames.value.filter((n) => n !== name)
  } else {
    selectedImportSeriesNames.value.push(name)
  }
}

async function handleClose() {
  if (props.tempToken) {
    try {
      await apiClient.post('/api/stickers/admin/import/cancel', {
        temp_token: props.tempToken
      })
    } catch (e) {
      // 忽略清理临时文件的错误
    }
  }
  emit('update:open', false)
  emit('close')
}

async function handleConfirmImportSubmit() {
  if (selectedImportSeriesNames.value.length === 0) {
    showToast('请至少勾选一个需要导入的贴纸系列！', 'warning')
    return
  }

  isImporting.value = true
  try {
    const res: any = await apiClient.post('/api/stickers/admin/import/confirm', {
      temp_token: props.tempToken,
      selected_series_names: selectedImportSeriesNames.value,
      conflict_resolution: importConflictResolution.value
    })
    showToast(res?.message || '贴纸包批量导入成功！', 'success')
    emit('update:open', false)
    emit('import-success')
  } catch (err: any) {
    const errMsg = err.response?.data?.detail || err.message || '导入落库失败，请重试'
    showToast(errMsg, 'error')
  } finally {
    isImporting.value = false
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
      style="display: flex; z-index: 1250;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-dialog-custom" style="max-width: 820px; width: 95%; padding: 25px 30px;" @click.stop>
        <div class="modal-header" style="border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">📥 贴纸包导入确认</span>
          <span style="font-size: 0.8rem; color: var(--text-muted);">{{ zipFileName }}</span>
        </div>

        <div style="margin-top: 15px;">
          <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-main); margin-bottom: 8px;">包含以下贴纸系列 (勾选需要导入的系列)：</div>
          <div style="max-height: 320px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding-right: 5px;">
            <div v-if="seriesList.length === 0" style="text-align: center; color: var(--text-muted); padding: 20px;">
              未扫描到任何有效的贴纸系列
            </div>
            <div
              v-for="s in seriesList"
              :key="s.series_name"
              style="background: rgba(255, 255, 255, 0.02); border: 1.5px solid var(--card-border); border-radius: 12px; padding: 12px 16px; display: flex; flex-direction: column; gap: 10px;"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <label style="display: inline-flex; align-items: center; gap: 8px; font-weight: 700; cursor: pointer; color: var(--text-main);">
                  <input
                    type="checkbox"
                    :checked="selectedImportSeriesNames.includes(s.series_name)"
                    style="width: 16px; height: 16px; accent-color: #7c3aed; cursor: pointer;"
                    @change="toggleImportSeriesSelect(s.series_name)"
                  />
                  <span>📁 {{ s.series_name }}</span>
                  <span v-if="s.is_name_conflict" style="background: #f59e0b; color: #000; font-size: 0.72rem; padding: 2px 7px; border-radius: 6px; font-weight: 700;">
                    ⚠️ 本地已存在同名系列
                  </span>
                </label>
                <span style="font-size: 0.75rem; color: var(--text-muted);">共 {{ s.sticker_count }} 张贴纸</span>
              </div>
              <div v-if="s.stickers && s.stickers.length > 0" style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px;">
                <div
                  v-for="(st, idx) in s.stickers"
                  :key="idx"
                  style="width: 44px; height: 44px; border-radius: 8px; background: rgba(0,0,0,0.2); border: 1px solid var(--card-border); display: flex; align-items: center; justify-content: center; flex-shrink: 0; padding: 4px;"
                  :title="st.name"
                >
                  <img :src="st.image_b64 || '/static/images/ic_launcher.png'" style="max-width: 100%; max-height: 100%; object-fit: contain;" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div style="margin-top: 18px; padding-top: 12px; border-top: 1px dashed rgba(255,255,255,0.1);">
          <div style="font-size: 0.82rem; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">⚙️ 遇到同名系列处理策略：</div>
          <div style="display: flex; gap: 20px; font-size: 0.82rem; color: var(--text-main); flex-wrap: wrap;">
            <label style="cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
              <input v-model="importConflictResolution" type="radio" value="rename" /> 自动重命名为 "名称 (导入)"
            </label>
            <label style="cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
              <input v-model="importConflictResolution" type="radio" value="merge" /> 追加/合并到现有同名系列
            </label>
            <label style="cursor: pointer; display: inline-flex; align-items: center; gap: 4px;">
              <input v-model="importConflictResolution" type="radio" value="skip" /> 跳过同名系列
            </label>
          </div>
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: flex-end; gap: 12px;">
          <button type="button" class="btn btn-secondary" style="width: 85px;" @click="handleClose">取消</button>
          <button type="button" class="btn btn-primary-purple" :disabled="isImporting" @click="handleConfirmImportSubmit">
            {{ isImporting ? '⏳ 正在写入落库...' : '🚀 确认导入已选系列' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
