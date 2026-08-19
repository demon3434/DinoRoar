<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  open: boolean
  initialType?: 'STICKER' | 'CANVAS_SET'
  currentSelectedId?: number | null
  stickerSeries: any[]
  canvasSeries: any[]
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'select', seriesId: number, targetType: 'STICKER' | 'CANVAS_SET'): void
}>()

const pickerType = ref<'STICKER' | 'CANVAS_SET'>('STICKER')
const pickerKeyword = ref('')
const selectedPickerSeriesId = ref<number | null>(null)

watch(
  () => props.open,
  (val) => {
    if (val) {
      pickerType.value = props.initialType || 'STICKER'
      selectedPickerSeriesId.value = props.currentSelectedId || null
      pickerKeyword.value = ''
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

function confirmPickerSelect() {
  if (selectedPickerSeriesId.value) {
    emit('select', selectedPickerSeriesId.value, pickerType.value)
  }
  handleClose()
}

const currentSeriesList = computed(() => {
  return pickerType.value === 'STICKER' ? props.stickerSeries : props.canvasSeries
})

const filteredPickerList = computed(() => {
  const kw = pickerKeyword.value.trim().toLowerCase()
  if (!kw) return currentSeriesList.value
  return currentSeriesList.value.filter((s: any) => s.name?.toLowerCase().includes(kw))
})

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
      style="display: flex; z-index: 1100;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick"
    >
      <div class="modal-dialog-custom" style="max-width: 960px; width: 95%; height: 84vh; max-height: 840px; display: flex; flex-direction: column; overflow: hidden; padding: 18px 24px; box-sizing: border-box; border-radius: 18px;" @click.stop>
        <!-- 抽屉顶部栏 -->
        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-shrink: 0; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); gap: 12px;">
          <div style="display: flex; align-items: center; gap: 14px; flex: 1; min-width: 0;">
            <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main); white-space: nowrap;">📁 选择优惠系列</span>
            <div style="font-size: 0.85rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ selectedPickerSeriesId ? `已选 ID: ${selectedPickerSeriesId}` : '尚未选择系列' }}
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 14px; flex-shrink: 0;">
            <button
              type="button"
              class="btn btn-primary-purple"
              style="height: 32px; padding: 0 16px; font-size: 0.82rem; font-weight: 700; border-radius: 8px;"
              @click="confirmPickerSelect"
            >
              ✓ 确认选择
            </button>
            <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
          </div>
        </div>

        <!-- 筛选与搜索 -->
        <div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 10px; border-bottom: 1px solid var(--card-border); padding-bottom: 8px; flex-shrink: 0;">
          <div style="display: flex; gap: 8px;">
            <button
              type="button"
              class="series-pill"
              :class="{ active: pickerType === 'STICKER' }"
              @click="pickerType = 'STICKER'"
            >
              🎨 贴纸系列
            </button>
            <button
              type="button"
              class="series-pill"
              :class="{ active: pickerType === 'CANVAS_SET' }"
              @click="pickerType = 'CANVAS_SET'"
            >
              🖼️ 画布系列
            </button>
          </div>
          <input
            v-model="pickerKeyword"
            type="text"
            class="form-control"
            placeholder="🔍 快速搜索系列名称..."
            style="width: 220px; height: 32px; font-size: 0.8rem; padding: 4px 10px;"
          />
        </div>

        <!-- 系列网格区 -->
        <div class="picker-grid" style="flex: 1; overflow-y: auto; padding: 6px 4px;">
          <div
            v-for="ser in filteredPickerList"
            :key="ser.id"
            class="picker-item-card"
            :class="{ selected: selectedPickerSeriesId === ser.id }"
            @click="selectedPickerSeriesId = ser.id"
          >
            <!-- 左上角红底白字数字胶囊 -->
            <div class="picker-count-badge">{{ ser.stickers?.length || ser.sets?.length || 0 }}</div>

            <!-- 右上角选中对勾 -->
            <div class="picker-check-badge">✓</div>

            <div class="picker-cover-box" :class="pickerType === 'STICKER' ? 'sticker-cover' : 'canvas-cover'">
              <img
                :src="pickerType === 'STICKER' ? (ser.stickers?.[0]?.image_url || '/static/images/ic_launcher.png') : (ser.sets?.[0]?.instances?.[0]?.image_url || '/static/images/default_canvases/default_canvas_16_9.png')"
                class="picker-cover-img"
              />
            </div>
            <div class="picker-item-name" :title="ser.name">{{ ser.name }}</div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.series-pill {
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.series-pill:hover {
  background: rgba(139, 92, 246, 0.1);
  color: #8b5cf6;
}

.series-pill.active {
  background: #8b5cf6;
  color: white;
  border-color: #8b5cf6;
}

.picker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
  gap: 12px;
  align-content: start;
}

.picker-item-card {
  background: rgba(255, 255, 255, 0.03);
  border: 2px solid transparent;
  border-radius: 12px;
  padding: 6px 6px 8px 6px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  user-select: none;
}

.picker-item-card:hover {
  transform: translateY(-2px);
  background: rgba(139, 92, 246, 0.05);
  border-color: rgba(139, 92, 246, 0.3);
}

.picker-item-card.selected {
  background: rgba(139, 92, 246, 0.12);
  border-color: #8b5cf6;
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.25);
}

.picker-count-badge {
  position: absolute;
  top: 5px;
  left: 5px;
  background: #ef4444;
  color: #ffffff;
  font-size: 0.68rem;
  font-weight: 800;
  line-height: 1;
  padding: 2px 6px;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(239, 68, 68, 0.4);
  z-index: 2;
}

.picker-check-badge {
  display: none;
  position: absolute;
  top: 5px;
  right: 5px;
  background: #8b5cf6;
  color: #ffffff;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  font-size: 0.65rem;
  font-weight: 800;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(139, 92, 246, 0.4);
  z-index: 2;
}

.picker-item-card.selected .picker-check-badge {
  display: flex;
}

.picker-cover-box {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 6px;
  position: relative;
}

.picker-cover-box.sticker-cover {
  aspect-ratio: 1 / 1;
  padding: 4px;
  box-sizing: border-box;
}

.picker-cover-box.canvas-cover {
  aspect-ratio: 16 / 10;
}

.picker-cover-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.2s ease;
}

.picker-cover-box.canvas-cover .picker-cover-img {
  object-fit: cover;
}

.picker-item-card:hover .picker-cover-img {
  transform: scale(1.05);
}

.picker-item-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 0 2px;
}
</style>
