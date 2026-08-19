<script setup lang="ts">
import { ref, computed } from 'vue'

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
  series: StickerSeries
  isExportMode: boolean
  isSelectedForExport: boolean
  editingSeriesId: number | null
}>()

const emit = defineEmits<{
  (e: 'click'): void
  (e: 'toggle-export'): void
  (e: 'start-rename', series: StickerSeries): void
  (e: 'submit-rename', newName: string): void
  (e: 'cancel-rename'): void
  (e: 'toggle-active', ev: Event): void
  (e: 'delete', ev: Event): void
  (e: 'dragstart', ev: DragEvent): void
  (e: 'dragover', ev: DragEvent): void
  (e: 'dragenter', ev: DragEvent): void
  (e: 'dragleave', ev: DragEvent): void
  (e: 'drop', ev: DragEvent): void
  (e: 'dragend'): void
}>()

const localEditName = ref(props.series.name)

const isBuiltinSeries = computed(() => props.series.name === '3D恐龙' || props.series.id === 1)

function handleStartRename() {
  localEditName.value = props.series.name
  emit('start-rename', props.series)
}

function handleSaveRename() {
  emit('submit-rename', localEditName.value)
}
</script>

<template>
  <div
    class="folder-card"
    :class="{
      'grayscale-active': !series.is_active,
      'export-mode-active': isExportMode,
      'export-selected': isExportMode && isSelectedForExport
    }"
    :draggable="!isExportMode && editingSeriesId !== series.id"
    @click="emit('click')"
    @dragstart="emit('dragstart', $event)"
    @dragover="emit('dragover', $event)"
    @dragenter="emit('dragenter', $event)"
    @dragleave="emit('dragleave', $event)"
    @drop="emit('drop', $event)"
    @dragend="emit('dragend')"
  >
    <!-- 左上角红底白字数量胶囊 -->
    <div class="folder-count-badge">{{ series.stickers?.length || 0 }}</div>

    <!-- 右上角：导出模式复选框 或 重命名铅笔图标 -->
    <input
      v-if="isExportMode"
      type="checkbox"
      class="card-export-checkbox"
      :checked="isSelectedForExport"
      @click.stop="emit('toggle-export')"
    />
    <div
      v-else
      class="rename-trigger"
      title="重命名分类"
      @click.stop="handleStartRename"
    >
      ✏️
    </div>

    <!-- 分类标题 -->
    <div class="folder-title-box" @click.stop>
      <div v-if="editingSeriesId === series.id" style="width: 85%;">
        <input
          v-model="localEditName"
          type="text"
          class="form-control"
          style="height: 28px; font-size: 0.8rem; text-align: center; padding: 2px 4px;"
          autofocus
          @blur="handleSaveRename"
          @keyup.enter="handleSaveRename"
          @keyup.esc="emit('cancel-rename')"
        />
      </div>
      <div v-else class="folder-name-text">
        <span>{{ series.name }}</span>
      </div>
    </div>

    <!-- 四宫格缩略图 -->
    <div class="folder-icon-wrapper">
      <div class="tianzi-grid">
        <div v-for="i in 4" :key="i" class="tianzi-cell">
          <img
            v-if="series.stickers && series.stickers[i - 1]"
            :src="series.stickers[i - 1].image_url"
            alt="preview"
          />
        </div>
      </div>
      <!-- 停用状态禁止图标角标 -->
      <div v-if="!series.is_active" class="folder-ban-badge" title="该系列已停用">
        🚫
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="folder-btn-bar" @click.stop>
      <div
        class="card-capsule-switch"
        :class="{ active: series.is_active }"
        :title="series.is_active ? '点击停用此系列' : '点击启用此系列'"
        @click="emit('toggle-active', $event)"
      >
        <span class="capsule-thumb"></span>
        <span class="capsule-text">{{ series.is_active ? '启用' : '停用' }}</span>
      </div>
      <button
        v-if="isBuiltinSeries"
        type="button"
        class="small-action-btn del-btn disabled"
        disabled
        title="系统内置贴纸系列不可删除，但可以停用"
        style="opacity: 0.3; cursor: not-allowed;"
      >
        删除
      </button>
      <button
        v-else
        type="button"
        class="small-action-btn del-btn"
        @click="emit('delete', $event)"
      >
        删除
      </button>
    </div>
  </div>
</template>
