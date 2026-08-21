<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import StickerImportModal from './components/StickerImportModal.vue'
import StickerUploadCropModal from './components/StickerUploadCropModal.vue'
import StickerDetailModal from './components/StickerDetailModal.vue'
import StickerSeriesCard from './components/StickerSeriesCard.vue'
import StickerAddSeriesModal from './components/StickerAddSeriesModal.vue'

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

const seriesList = ref<StickerSeries[]>([])
const loading = ref(false)
const searchKeyword = ref('')

// 导出模式状态
const isExportMode = ref(false)
const selectedExportSeriesIds = ref<number[]>([])

// 选中的当前系列（用于详情弹窗）
const currentDetailSeries = ref<StickerSeries | null>(null)
const isDetailModalOpen = ref(false)

// 各种弹窗控制
const isAddSeriesModalOpen = ref(false)
const isAddStickerModalOpen = ref(false)
const isDeleteSeriesModalOpen = ref(false)
const isDeleteSingleStickerModalOpen = ref(false)
const seriesToDelete = ref<StickerSeries | null>(null)
const stickerToDelete = ref<StickerItem | null>(null)

// 原地重命名状态
const editingSeriesId = ref<number | null>(null)

// 导入贴纸包预览状态
interface ImportSeriesItem {
  series_name: string
  sticker_count: number
  is_name_conflict: boolean
  stickers: { name: string; image_b64: string }[]
}

const isImportPreviewModalOpen = ref(false)
const importTempToken = ref('')
const importZipFileName = ref('')
const importSeriesList = ref<ImportSeriesItem[]>([])
const importZipInputRef = ref<HTMLInputElement | null>(null)

// 拖拽排序状态
let draggedSeries: StickerSeries | null = null

const filteredSeries = computed(() => {
  if (!searchKeyword.value.trim()) return seriesList.value
  const kw = searchKeyword.value.trim().toLowerCase()
  return seriesList.value.filter(
    (s) => s.name.toLowerCase().includes(kw) || s.stickers?.some((stk) => stk.name.toLowerCase().includes(kw))
  )
})

const defaultStickerSort = computed(() => {
  const stickers = currentDetailSeries.value?.stickers || []
  if (stickers.length === 0) return 1
  const maxSort = stickers.reduce((max, s) => Math.max(max, Number(s.sort_order) || 0), 0)
  return maxSort + 1
})

const defaultSeriesSort = computed(() => {
  if (seriesList.value.length === 0) return 1
  const maxSort = seriesList.value.reduce((max, s) => Math.max(max, Number(s.sort_order) || 0), 0)
  return maxSort + 1
})

async function loadData() {
  loading.value = true
  try {
    const res: any = await apiClient.get('/api/stickers/config?for_admin=true')
    seriesList.value = res || []
    if (currentDetailSeries.value) {
      const refreshed = seriesList.value.find((s) => s.id === currentDetailSeries.value!.id)
      if (refreshed) {
        currentDetailSeries.value = refreshed
      }
    }
  } catch (e: any) {
    showToast('加载贴纸系列失败', 'error')
  } finally {
    loading.value = false
  }
}

function openDetailModal(series: StickerSeries) {
  if (editingSeriesId.value === series.id) return
  if (isExportMode.value) {
    toggleExportSelect(series.id)
    return
  }
  currentDetailSeries.value = series
  isDetailModalOpen.value = true
}

// 启停系列
async function handleToggleSeriesActive(e: Event, series: StickerSeries) {
  e.stopPropagation()
  try {
    const res: any = await apiClient.post(`/api/stickers/admin/series/${series.id}/toggle-active`, {
      is_active: !series.is_active
    })
    series.is_active = res.is_active
    showToast(series.is_active ? `已启用「${series.name}」` : `已停用「${series.name}」`, 'info')
  } catch (e: any) {
    showToast('更新状态失败', 'error')
  }
}

// 删除系列提示
function promptDeleteSeries(e: Event, series: StickerSeries) {
  e.stopPropagation()
  if (series.name === '3D恐龙' || series.id === 1) {
    showToast('系统内置贴纸系列不可删除，但可以停用', 'warning')
    return
  }
  seriesToDelete.value = series
  isDeleteSeriesModalOpen.value = true
}

async function confirmDeleteSeries() {
  if (!seriesToDelete.value) return
  if (seriesToDelete.value.name === '3D恐龙' || seriesToDelete.value.id === 1) {
    showToast('系统内置贴纸系列不可删除，但可以停用', 'warning')
    isDeleteSeriesModalOpen.value = false
    seriesToDelete.value = null
    return
  }
  try {
    await apiClient.delete(`/api/stickers/admin/series/${seriesToDelete.value.id}`)
    showToast(`已删除系列「${seriesToDelete.value.name}」`, 'success')
    isDeleteSeriesModalOpen.value = false
    seriesToDelete.value = null
    await loadData()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '删除系列失败', 'error')
  }
}

// 删除单张贴纸提示
function promptDeleteSingleSticker(sticker: StickerItem) {
  if (currentDetailSeries.value?.name === '3D恐龙' || currentDetailSeries.value?.id === 1) {
    showToast('系统内置贴纸不可删除，但可以停用', 'warning')
    return
  }
  stickerToDelete.value = sticker
  isDeleteSingleStickerModalOpen.value = true
}

async function confirmDeleteSingleSticker() {
  if (!stickerToDelete.value) return
  if (currentDetailSeries.value?.name === '3D恐龙' || currentDetailSeries.value?.id === 1) {
    showToast('系统内置贴纸不可删除，但可以停用', 'warning')
    isDeleteSingleStickerModalOpen.value = false
    stickerToDelete.value = null
    return
  }
  try {
    await apiClient.delete(`/api/stickers/admin/stickers/${stickerToDelete.value.id}`)
    showToast(`已删除贴纸「${stickerToDelete.value.name}」`, 'success')
    isDeleteSingleStickerModalOpen.value = false
    stickerToDelete.value = null
    await loadData()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '删除贴纸失败', 'error')
  }
}

// 新建系列
async function handleCreateSeries(data: { name: string; sort_order: number }) {
  try {
    await apiClient.post('/api/stickers/admin/series', data)
    showToast('贴纸系列创建成功！', 'success')
    isAddSeriesModalOpen.value = false
    await loadData()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '创建系列失败', 'error')
  }
}

// 重命名系列
function startRenameSeries(series: StickerSeries) {
  editingSeriesId.value = series.id
}

async function handleSaveSeriesRename(newName: string) {
  if (!editingSeriesId.value) return
  const id = editingSeriesId.value
  const target = seriesList.value.find((s) => s.id === id)
  if (!target) {
    editingSeriesId.value = null
    return
  }

  const trimmed = newName.trim()
  if (!trimmed) {
    showToast('系列名称不能为空！', 'warning')
    editingSeriesId.value = null
    return
  }

  if (trimmed === target.name) {
    editingSeriesId.value = null
    return
  }

  const oldName = target.name
  target.name = trimmed
  try {
    await apiClient.put(`/api/stickers/admin/series/${id}`, { name: trimmed })
    showToast(`系列已重命名为「${trimmed}」`, 'success')
  } catch (err: any) {
    target.name = oldName
    showToast(err.response?.data?.detail || '重命名失败', 'error')
  } finally {
    editingSeriesId.value = null
  }
}

function handleCancelSeriesRename() {
  editingSeriesId.value = null
}

// 导出模式
function toggleExportMode() {
  isExportMode.value = !isExportMode.value
  selectedExportSeriesIds.value = []
}

function toggleExportSelect(seriesId: number) {
  if (selectedExportSeriesIds.value.includes(seriesId)) {
    selectedExportSeriesIds.value = selectedExportSeriesIds.value.filter((id) => id !== seriesId)
  } else {
    selectedExportSeriesIds.value.push(seriesId)
  }
}

function toggleSelectAllExport() {
  if (selectedExportSeriesIds.value.length === filteredSeries.value.length) {
    selectedExportSeriesIds.value = []
  } else {
    selectedExportSeriesIds.value = filteredSeries.value.map((s) => s.id)
  }
}

async function handleExportSubmit() {
  if (selectedExportSeriesIds.value.length === 0) {
    showToast('请至少选择一个需要导出的系列！', 'warning')
    return
  }
  try {
    const res: any = await apiClient.post(
      '/api/stickers/admin/export',
      { series_ids: selectedExportSeriesIds.value },
      { responseType: 'blob' }
    )
    const blob = new Blob([res], { type: 'application/zip' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `dinoroar_stickers_export_${new Date().toISOString().slice(0, 10)}.zip`
    link.click()
    URL.revokeObjectURL(link.href)
    showToast('贴纸包已成功生成并下载！', 'success')
    isExportMode.value = false
    selectedExportSeriesIds.value = []
  } catch (err: any) {
    showToast('导出贴纸包失败，请重试', 'error')
  }
}

// 导入 ZIP
function triggerImportZipFile() {
  if (importZipInputRef.value) {
    importZipInputRef.value.value = ''
    importZipInputRef.value.click()
  }
}

async function handleImportZipFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files || !target.files[0]) return
  const file = target.files[0]
  if (!file.name.toLowerCase().endsWith('.zip')) {
    showToast('请上传标准的 .zip 格式压缩包！', 'warning')
    return
  }

  const formData = new FormData()
  formData.append('file', file)

  try {
    showToast('正在解析贴纸包，请稍候...', 'info')
    const res: any = await apiClient.post('/api/stickers/admin/import/preview', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importTempToken.value = res.temp_token
    importZipFileName.value = file.name
    importSeriesList.value = res.series_list || []
    isImportPreviewModalOpen.value = true
  } catch (err: any) {
    const errMsg = err.response?.data?.detail || err.message || '解析贴纸压缩包失败'
    showToast(errMsg, 'error')
  }
}

// 系列拖拽排序
function handleSeriesDragStart(e: DragEvent, series: StickerSeries) {
  if (isExportMode.value) return
  draggedSeries = series
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', String(series.id))
  }
}

function handleSeriesDragOver(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

function handleSeriesDragEnter(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.folder-card')
  if (target) target.classList.add('over')
}

function handleSeriesDragLeave(e: DragEvent) {
  const target = (e.target as HTMLElement).closest('.folder-card')
  if (target) target.classList.remove('over')
}

async function handleSeriesDrop(e: DragEvent, targetSeries: StickerSeries) {
  e.preventDefault()
  const target = (e.target as HTMLElement).closest('.folder-card')
  if (target) target.classList.remove('over')

  if (!draggedSeries || draggedSeries.id === targetSeries.id) return

  const list = [...seriesList.value]
  const fromIdx = list.findIndex((s) => s.id === draggedSeries!.id)
  const toIdx = list.findIndex((s) => s.id === targetSeries.id)

  if (fromIdx !== -1 && toIdx !== -1) {
    const [moved] = list.splice(fromIdx, 1)
    list.splice(toIdx, 0, moved)
    seriesList.value = list

    const orderedIds = list.map((s) => s.id)
    try {
      await apiClient.post('/api/stickers/admin/series/reorder', { ordered_ids: orderedIds })
      showToast('系列排序更新成功！', 'success')
    } catch (err) {
      showToast('更新系列排序失败', 'error')
    }
  }
  draggedSeries = null
}

function handleSeriesDragEnd() {
  document.querySelectorAll('.folder-card.over').forEach((el) => el.classList.remove('over'))
  draggedSeries = null
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="content-container">
    <input
      ref="importZipInputRef"
      type="file"
      accept=".zip"
      style="display: none;"
      @change="handleImportZipFileSelect"
    />

    <!-- 顶部操作栏 (严格对齐 194 原版) -->
    <header style="display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap; margin-bottom: 24px;">
      <div>
        <h2 style="font-size: 1.4rem; font-weight: 800; margin: 0; color: var(--text-main);">🎨 贴纸管理</h2>
      </div>

      <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="🔍 搜索筛选..."
          class="form-control"
          style="width: 150px; height: 38px; margin: 0; font-size: 0.82rem;"
        />

        <div v-if="!isExportMode" style="display: flex; gap: 12px; align-items: center;">
          <button class="btn-outline-purple" style="margin: 0; white-space: nowrap; height: 38px; padding: 0 14px;" @click="triggerImportZipFile">
            📥 导入贴纸包
          </button>
          <button class="btn-outline-purple" style="margin: 0; white-space: nowrap; height: 38px; padding: 0 14px;" @click="toggleExportMode">
            📦 批量导出
          </button>
          <button class="btn btn-primary-purple" style="margin: 0; white-space: nowrap; height: 38px; padding: 0 16px;" @click="isAddSeriesModalOpen = true">
            + 新建系列
          </button>
        </div>

        <div v-else style="display: flex; gap: 12px; align-items: center;">
          <label style="font-size: 0.82rem; cursor: pointer; color: #7c3aed; font-weight: 800; display: inline-flex; align-items: center; gap: 4px;">
            <input
              type="checkbox"
              :checked="selectedExportSeriesIds.length === filteredSeries.length && filteredSeries.length > 0"
              style="accent-color: #7c3aed; width: 16px; height: 16px; cursor: pointer;"
              @change="toggleSelectAllExport"
            /> 全选
          </label>
          <button class="btn btn-primary-purple" style="margin: 0; white-space: nowrap; height: 38px; padding: 0 16px;" @click="handleExportSubmit">
            🚀 确认导出 ({{ selectedExportSeriesIds.length }})
          </button>
          <button class="logout-btn" style="margin: 0; white-space: nowrap; height: 38px; padding: 0 14px;" @click="toggleExportMode">
            退出导出
          </button>
        </div>
      </div>
    </header>

    <!-- 加载与空状态 -->
    <div v-if="loading" style="text-align: center; padding: 60px; color: var(--text-muted);">
      <div class="spinner" style="margin: 0 auto 12px;"></div>
      加载贴纸系列中...
    </div>

    <div v-else-if="filteredSeries.length === 0" style="text-align: center; padding: 60px; color: var(--text-muted);">
      <span style="font-size: 2.5rem; display: block; margin-bottom: 12px; opacity: 0.6;">📂</span>
      未找到任何贴纸系列
    </div>

    <!-- 系列文件夹网格流 -->
    <div v-else class="folder-grid">
      <StickerSeriesCard
        v-for="series in filteredSeries"
        :key="series.id"
        :series="series"
        :is-export-mode="isExportMode"
        :is-selected-for-export="selectedExportSeriesIds.includes(series.id)"
        :editing-series-id="editingSeriesId"
        @click="openDetailModal(series)"
        @toggle-active="handleToggleSeriesActive($event, series)"
        @delete="promptDeleteSeries($event, series)"
        @start-rename="startRenameSeries"
        @submit-rename="handleSaveSeriesRename"
        @cancel-rename="editingSeriesId = null"
        @toggle-export="toggleExportSelect(series.id)"
        @dragstart="handleSeriesDragStart($event, series)"
        @dragover="handleSeriesDragOver"
        @dragenter="handleSeriesDragEnter"
        @dragleave="handleSeriesDragLeave"
        @drop="handleSeriesDrop($event, series)"
        @dragend="handleSeriesDragEnd"
      />
    </div>

    <!-- 1. 文件夹详情弹窗 -->
    <StickerDetailModal
      v-model:open="isDetailModalOpen"
      :series="currentDetailSeries"
      @open-add-sticker="isAddStickerModalOpen = true"
      @prompt-delete-single="promptDeleteSingleSticker"
      @reorder-success="loadData"
      @batch-delete-success="loadData"
    />

    <!-- 2. 新建系列弹窗 -->
    <StickerAddSeriesModal
      v-model="isAddSeriesModalOpen"
      :default-sort-order="defaultSeriesSort"
      @confirm="handleCreateSeries"
    />

    <!-- 3. 新增贴纸弹窗 (Cropper.js) -->
    <StickerUploadCropModal
      v-model:open="isAddStickerModalOpen"
      :series-id="currentDetailSeries?.id || null"
      :series-name="currentDetailSeries?.name"
      :default-sort-order="defaultStickerSort"
      @created="loadData"
    />

    <!-- 删除系列确认 -->
    <ConfirmModal
      v-model="isDeleteSeriesModalOpen"
      title="删除贴纸系列确认"
      :message="`确定要删除系列「${seriesToDelete?.name}」吗？系列下的所有贴纸将被彻底清除！`"
      confirm-text="确认删除"
      type="danger"
      @confirm="confirmDeleteSeries"
    />

    <!-- 删除单张贴纸确认 -->
    <ConfirmModal
      v-model="isDeleteSingleStickerModalOpen"
      title="删除贴纸确认"
      :message="`确定要删除贴纸「${stickerToDelete?.name}」吗？`"
      confirm-text="确认删除"
      type="danger"
      @confirm="confirmDeleteSingleSticker"
    />

    <!-- 贴纸包导入预览与确认弹窗 -->
    <StickerImportModal
      v-model:open="isImportPreviewModalOpen"
      :zip-file-name="importZipFileName"
      :temp-token="importTempToken"
      :series-list="importSeriesList"
      @import-success="loadData"
    />
  </div>
</template>
