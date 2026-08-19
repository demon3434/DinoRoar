<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

interface ImportCanvasInstance {
  aspect_ratio: string
  image_b64?: string
  file_path?: string
  width?: number
  height?: number
}

interface ImportCanvasSet {
  name: string
  description?: string
  exchange_price: number
  sort_order?: number
  instances: ImportCanvasInstance[]
  activeRatio?: string
}

interface ImportCanvasSeries {
  series_name: string
  dir_name?: string
  set_count: number
  is_name_conflict: boolean
  canvas_sets: ImportCanvasSet[]
  isExpanded?: boolean
}

const props = defineProps<{
  open: boolean
  zipFileName: string
  tempToken: string
  seriesList: ImportCanvasSeries[]
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'import-success'): void
  (e: 'close'): void
}>()

// 记录选中的套件映射: { [seriesName]: [setName1, setName2, ...] }
const selectedSetsMap = ref<Record<string, string[]>>({})
const importConflictResolution = ref<'rename' | 'merge' | 'skip'>('rename')
const isImporting = ref(false)

// 内部维护系列展开状态
const localSeriesList = ref<ImportCanvasSeries[]>([])

// Lightbox 全屏大图查看状态
const isLightboxOpen = ref(false)
const lightboxImageUrl = ref('')
const lightboxTitle = ref('')
const lightboxScale = ref(1)

function openLightbox(url: string, title: string) {
  lightboxImageUrl.value = url
  lightboxTitle.value = title
  lightboxScale.value = 1
  isLightboxOpen.value = true
}

function closeLightbox() {
  isLightboxOpen.value = false
}

function zoomInLightbox() {
  lightboxScale.value = Math.min(lightboxScale.value + 0.25, 3.0)
}

function zoomOutLightbox() {
  lightboxScale.value = Math.max(lightboxScale.value - 0.25, 0.5)
}

function resetLightboxZoom() {
  lightboxScale.value = 1
}

watch(
  () => props.seriesList,
  (list) => {
    const map: Record<string, string[]> = {}
    localSeriesList.value = (list || []).map((s) => {
      map[s.series_name] = (s.canvas_sets || []).map((cs) => cs.name)
      return {
        ...s,
        isExpanded: true,
        canvas_sets: (s.canvas_sets || []).map((cs) => ({
          ...cs,
          activeRatio: cs.activeRatio || (cs.instances?.[0]?.aspect_ratio || '16:9')
        }))
      }
    })
    selectedSetsMap.value = map
  },
  { immediate: true }
)

const totalAvailableSetsCount = computed(() => {
  return localSeriesList.value.reduce((acc, s) => acc + (s.canvas_sets?.length || 0), 0)
})

const totalSelectedSetsCount = computed(() => {
  let count = 0
  for (const s of localSeriesList.value) {
    const list = selectedSetsMap.value[s.series_name] || []
    count += list.length
  }
  return count
})

function isSetSelected(seriesName: string, setName: string): boolean {
  return (selectedSetsMap.value[seriesName] || []).includes(setName)
}

function toggleSetSelect(seriesName: string, setName: string) {
  if (!selectedSetsMap.value[seriesName]) {
    selectedSetsMap.value[seriesName] = []
  }
  const list = selectedSetsMap.value[seriesName]
  const idx = list.indexOf(setName)
  if (idx > -1) {
    list.splice(idx, 1)
  } else {
    list.push(setName)
  }
}

function isSeriesAllSelected(s: ImportCanvasSeries): boolean {
  if (!s.canvas_sets || s.canvas_sets.length === 0) return false
  const selected = selectedSetsMap.value[s.series_name] || []
  return selected.length === s.canvas_sets.length
}

function isSeriesIndeterminate(s: ImportCanvasSeries): boolean {
  const selected = selectedSetsMap.value[s.series_name] || []
  return selected.length > 0 && selected.length < (s.canvas_sets?.length || 0)
}

function toggleSeriesAllSelect(s: ImportCanvasSeries) {
  const allSelected = isSeriesAllSelected(s)
  if (allSelected) {
    selectedSetsMap.value[s.series_name] = []
  } else {
    selectedSetsMap.value[s.series_name] = (s.canvas_sets || []).map((cs) => cs.name)
  }
}

function toggleGlobalAllSelect() {
  const allSelected = totalSelectedSetsCount.value === totalAvailableSetsCount.value && totalAvailableSetsCount.value > 0
  const map: Record<string, string[]> = {}
  for (const s of localSeriesList.value) {
    map[s.series_name] = allSelected ? [] : (s.canvas_sets || []).map((cs) => cs.name)
  }
  selectedSetsMap.value = map
}

function getImportSetPreviewImage(cs: ImportCanvasSet): string {
  const ratio = cs.activeRatio || '16:9'
  const inst = cs.instances?.find((i) => i.aspect_ratio === ratio) || cs.instances?.[0]
  return inst?.image_b64 || '/static/images/default_canvases/default_canvas_16_9.png'
}

function getImportSetPreviewFilePath(cs: ImportCanvasSet): string {
  const ratio = cs.activeRatio || '16:9'
  const inst = cs.instances?.find((i) => i.aspect_ratio === ratio) || cs.instances?.[0]
  return inst?.file_path || ''
}

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

async function handleClose() {
  if (props.tempToken) {
    try {
      await apiClient.post('/api/canvases/admin/import/cancel', {
        temp_token: props.tempToken
      })
    } catch (e) {}
  }
  emit('update:open', false)
  emit('close')
}

async function handleConfirmImportSubmit() {
  const selectedSeriesNames: string[] = []
  const selectedSetsMapPayload: Record<string, string[]> = {}

  for (const s of localSeriesList.value) {
    const sets = selectedSetsMap.value[s.series_name] || []
    if (sets.length > 0) {
      selectedSeriesNames.push(s.series_name)
      selectedSetsMapPayload[s.series_name] = sets
    }
  }

  if (selectedSeriesNames.length === 0 || totalSelectedSetsCount.value === 0) {
    showToast('请至少勾选一个需要导入的画布套件！', 'warning')
    return
  }

  isImporting.value = true
  try {
    const res: any = await apiClient.post('/api/canvases/admin/import/confirm', {
      temp_token: props.tempToken,
      selected_series_names: selectedSeriesNames,
      conflict_resolution: importConflictResolution.value,
      selected_sets_map: selectedSetsMapPayload
    })
    showToast(res?.message || `成功导入 ${totalSelectedSetsCount.value} 套画布！`, 'success')
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
  if (e.key === 'Escape') {
    if (isLightboxOpen.value) {
      closeLightbox()
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
      v-if="open"
      class="modal"
      style="display: flex; z-index: 1250;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div
        class="modal-dialog-custom"
        style="max-width: 1060px; width: 95%; height: 88vh; max-height: 860px; display: flex; flex-direction: column; overflow: hidden; padding: 22px 28px; box-sizing: border-box; border-radius: 18px;"
        @click.stop
      >
        <!-- 弹窗 Header -->
        <div class="modal-header" style="border-bottom: 1px solid var(--card-border); padding-bottom: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;">
          <div style="display: flex; align-items: baseline; gap: 10px;">
            <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">📥 画布包导入确认</span>
            <span style="font-size: 0.8rem; color: var(--text-muted);">{{ zipFileName }}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 14px;">
            <span style="font-size: 0.85rem; font-weight: 700; color: #8b5cf6;">
              已选 {{ totalSelectedSetsCount }} / {{ totalAvailableSetsCount }} 套画布
            </span>
            <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
          </div>
        </div>

        <!-- 顶部操作条：全选控制 Checkbox -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-shrink: 0;">
          <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-main);">
            请勾选需要导入的系列及画布套件：
          </div>
          <label style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 700; color: var(--text-main); cursor: pointer; user-select: none;">
            <input
              type="checkbox"
              :checked="totalSelectedSetsCount === totalAvailableSetsCount && totalAvailableSetsCount > 0"
              :indeterminate="totalSelectedSetsCount > 0 && totalSelectedSetsCount < totalAvailableSetsCount"
              style="width: 16px; height: 16px; accent-color: #7c3aed; cursor: pointer;"
              @change="toggleGlobalAllSelect"
            />
            <span>全部全选</span>
          </label>
        </div>

        <!-- 手风琴可滚动列表容器 -->
        <div class="import-series-scroll-container">
          <div v-if="localSeriesList.length === 0" style="text-align: center; color: var(--text-muted); padding: 40px;">
            未扫描到任何有效的画布套件
          </div>

          <div
            v-for="s in localSeriesList"
            :key="s.series_name"
            class="import-series-accordion-card"
          >
            <!-- 手风琴折叠头部 -->
            <div
              class="accordion-header"
              @click="s.isExpanded = !s.isExpanded"
            >
              <div style="display: flex; align-items: center; gap: 10px;">
                <input
                  type="checkbox"
                  :checked="isSeriesAllSelected(s)"
                  :indeterminate="isSeriesIndeterminate(s)"
                  style="width: 16px; height: 16px; accent-color: #7c3aed; cursor: pointer;"
                  @click.stop
                  @change="toggleSeriesAllSelect(s)"
                />
                <span style="font-weight: 800; font-size: 0.95rem; color: var(--text-main);">📁 {{ s.series_name }}</span>
                <span v-if="s.is_name_conflict" style="background: #f59e0b; color: #000; font-size: 0.72rem; padding: 2px 7px; border-radius: 6px; font-weight: 700;">
                  ⚠️ 本地已存在同名系列
                </span>
              </div>
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 0.8rem; color: var(--text-muted);">
                  已选 {{ (selectedSetsMap[s.series_name] || []).length }} / {{ s.canvas_sets?.length || 0 }} 套
                </span>
                <span
                  class="accordion-arrow"
                  :style="{ transform: s.isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }"
                >
                  ▼
                </span>
              </div>
            </div>

            <!-- 手风琴折叠内容区 (网格卡片) -->
            <div v-show="s.isExpanded" class="accordion-content">
              <div class="cards-grid">
                <div
                  v-for="cs in s.canvas_sets"
                  :key="cs.name"
                  class="import-set-card"
                  :class="{ selected: isSetSelected(s.series_name, cs.name) }"
                  @click="toggleSetSelect(s.series_name, cs.name)"
                >
                  <!-- 卡片顶部：勾选框 + 套件名称 -->
                  <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;" @click.stop>
                    <label style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 700; color: var(--text-main); cursor: pointer; flex: 1; min-width: 0;">
                      <input
                        type="checkbox"
                        :checked="isSetSelected(s.series_name, cs.name)"
                        style="width: 15px; height: 15px; accent-color: #7c3aed; cursor: pointer; flex-shrink: 0;"
                        @change="toggleSetSelect(s.series_name, cs.name)"
                      />
                      <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" :title="cs.name">{{ cs.name }}</span>
                    </label>
                    <span style="font-size: 0.75rem; color: #8b5cf6; font-weight: 700; flex-shrink: 0;">🥚 {{ cs.exchange_price || 50 }}</span>
                  </div>

                  <!-- 缩略图区域 (点击可大图预览) -->
                  <div
                    class="card-preview-container"
                    title="点击放大预览"
                    @click.stop="openLightbox(getImportSetPreviewFilePath(cs) ? `/api/canvases/admin/import/preview-file?temp_token=${encodeURIComponent(tempToken)}&file_path=${encodeURIComponent(getImportSetPreviewFilePath(cs))}` : getImportSetPreviewImage(cs), `${s.series_name} - ${cs.name} (${cs.activeRatio || '16:9'})`)"
                  >
                    <img
                      :src="getImportSetPreviewImage(cs)"
                      class="card-preview-image"
                      alt="canvas preview"
                    />
                    <div class="zoom-badge">
                      🔍 放大
                    </div>
                  </div>

                  <!-- 比例切换按钮栏 -->
                  <div class="ratio-button-group" @click.stop>
                    <button
                      v-for="r in ['16:9', '4:3', '1:1', '3:4']"
                      :key="r"
                      type="button"
                      class="small-ratio-btn"
                      :class="{ active: (cs.activeRatio || '16:9') === r }"
                      @click="cs.activeRatio = r"
                    >
                      {{ r }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 冲突处理策略栏 -->
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px dashed rgba(255,255,255,0.1); flex-shrink: 0;">
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

        <!-- 弹窗底部操作按钮 -->
        <div style="margin-top: 14px; display: flex; justify-content: flex-end; gap: 12px; flex-shrink: 0;">
          <button type="button" class="btn btn-secondary" style="width: 85px;" @click="handleClose">取消</button>
          <button type="button" class="btn btn-primary-purple" :disabled="isImporting" @click="handleConfirmImportSubmit">
            {{ isImporting ? '⏳ 正在写入落库...' : `🚀 确认导入已选 (${totalSelectedSetsCount}) 套画布` }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 全屏大图查看 Lightbox 模态框 -->
  <Teleport to="body">
    <div
      v-if="isLightboxOpen"
      class="modal"
      style="display: flex; z-index: 1500; background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px);"
      @click="closeLightbox"
    >
      <div
        style="position: relative; max-width: 90vw; max-height: 90vh; display: flex; flex-direction: column; align-items: center; justify-content: center;"
        @click.stop
      >
        <!-- Lightbox 顶部控制栏 -->
        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 12px; color: #fff;">
          <span style="font-weight: 700; font-size: 1rem;">🖼️ {{ lightboxTitle }}</span>
          <div style="display: flex; gap: 10px; align-items: center;">
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="zoomInLightbox">放大 🔍+</button>
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="zoomOutLightbox">缩小 🔍-</button>
            <button class="btn-outline-purple" style="padding: 2px 10px; font-size: 0.8rem; height: 28px;" @click="resetLightboxZoom">1:1 重置</button>
            <span class="modal-close-icon" title="关闭" style="margin-left: 8px;" @click="closeLightbox">✕</span>
          </div>
        </div>

        <!-- 大图展示区 -->
        <div style="overflow: auto; max-width: 100%; max-height: 80vh; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: #09090b; display: flex; align-items: center; justify-content: center; padding: 10px;">
          <img
            :src="lightboxImageUrl"
            :style="{ transform: `scale(${lightboxScale})`, transition: 'transform 0.15s ease-out' }"
            style="max-width: 80vw; max-height: 75vh; object-fit: contain; transform-origin: center center;"
            alt="Full size canvas"
          />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.import-series-scroll-container {
  flex: 1 1 0px !important;
  min-height: 0 !important;
  overflow-y: auto !important;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 6px;
  box-sizing: border-box;
}

.import-series-accordion-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1.5px solid var(--card-border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.accordion-header {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.03);
  user-select: none;
  transition: background 0.2s;
}

.accordion-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.accordion-arrow {
  font-size: 0.85rem;
  color: var(--text-muted);
  transition: transform 0.2s;
}

.accordion-content {
  padding: 12px 14px;
  border-top: 1px solid var(--card-border);
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.import-set-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1.5px solid var(--card-border);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: all 0.2s;
  cursor: pointer;
}

.import-set-card:hover {
  border-color: rgba(139, 92, 246, 0.5);
  transform: translateY(-2px);
}

.import-set-card.selected {
  border-color: #8b5cf6 !important;
  background: rgba(139, 92, 246, 0.08) !important;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.15);
}

.card-preview-container {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 6px;
  overflow: hidden;
  background: #18181b;
  cursor: zoom-in;
  position: relative;
  border: 1px solid var(--card-border);
}

.card-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.zoom-badge {
  position: absolute;
  bottom: 3px;
  right: 3px;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  font-size: 0.65rem;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
}

.ratio-button-group {
  display: flex;
  gap: 3px;
  width: 100%;
}

.small-ratio-btn {
  flex: 1;
  padding: 3px 0;
  font-size: 0.68rem;
  font-weight: 600;
  border-radius: 4px;
  border: 1px solid var(--card-border);
  cursor: pointer;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
  transition: all 0.15s;
}

.small-ratio-btn:hover {
  color: var(--text-main);
  border-color: rgba(139, 92, 246, 0.4);
}

.small-ratio-btn.active {
  background: #8b5cf6 !important;
  color: #fff !important;
  border-color: #8b5cf6 !important;
}
</style>
