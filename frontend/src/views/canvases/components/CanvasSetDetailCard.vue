<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  set: any
  activeRatio: string
  isBatchDeleteMode: boolean
  isSelectedForDelete: boolean
}>()

const emit = defineEmits<{
  (e: 'select-ratio', ratio: string): void
  (e: 'toggle-delete'): void
  (e: 'open-lightbox', url: string, title: string): void
  (e: 'open-edit', set: any): void
  (e: 'open-upload', set: any, ratio: string): void
  (e: 'toggle-active', ev: Event, set: any): void
  (e: 'delete', ev: Event, set: any): void
  (e: 'dragstart', ev: DragEvent): void
  (e: 'dragover', ev: DragEvent): void
  (e: 'dragenter', ev: DragEvent): void
  (e: 'dragleave', ev: DragEvent): void
  (e: 'drop', ev: DragEvent): void
  (e: 'dragend'): void
}>()

const ratios = ['16:9', '4:3', '1:1', '2:1']

function getInstanceByRatio(ratio: string) {
  return props.set.instances?.find((inst: any) => inst.aspect_ratio === ratio && !inst.is_deleted)
}

const isBuiltinSet = computed(() => props.set.id === 3001 || props.set.name === '森林家园')

const currentPreviewUrl = computed(() => {
  const inst = getInstanceByRatio(props.activeRatio)
  return inst?.image_url || ''
})
</script>

<template>
  <div
    class="set-detail-card"
    :class="{
      'grayscale-active': !set.is_active,
      'batch-selected': isSelectedForDelete
    }"
    :draggable="!isBatchDeleteMode"
    @dragstart="emit('dragstart', $event)"
    @dragover="emit('dragover', $event)"
    @dragenter="emit('dragenter', $event)"
    @dragleave="emit('dragleave', $event)"
    @drop="emit('drop', $event)"
    @dragend="emit('dragend')"
  >
    <!-- 批量删除勾选复选框 -->
    <div
      v-if="isBatchDeleteMode"
      class="batch-delete-checkbox-box"
      :title="isBuiltinSet ? '内置预设底图不可删除' : '勾选删除'"
      @click.stop="isBuiltinSet ? null : emit('toggle-delete')"
    >
      <input
        type="checkbox"
        :checked="isSelectedForDelete"
        :disabled="isBuiltinSet"
        style="accent-color: #ef4444; width: 18px; height: 18px;"
        :style="isBuiltinSet ? 'opacity: 0.3; cursor: not-allowed;' : 'cursor: pointer;'"
      />
    </div>

    <!-- 1. 预览图与横幅 -->
    <div class="set-card-preview-box">
      <img
        v-if="currentPreviewUrl"
        :src="currentPreviewUrl"
        :alt="set.name"
        class="set-card-preview-img"
        draggable="false"
        @click.stop="emit('open-lightbox', currentPreviewUrl, `${set.name} (${activeRatio})`)"
      />
      <div v-else class="set-card-empty-tip">未上传该比例</div>

      <!-- 底部名称与蛋能量价格标签 -->
      <div class="set-card-title-banner">
        <span class="set-card-name-banner" :title="set.name">{{ set.name }}</span>
        <span class="set-card-price-banner">🥚 {{ set.exchange_price }}</span>
      </div>
    </div>

    <!-- 2. 4 种比例快速切换选项卡 -->
    <div class="ratio-switcher-row">
      <button
        v-for="r in ratios"
        :key="r"
        type="button"
        class="btn-ratio-switch"
        :class="{
          active: activeRatio === r,
          'has-image': !!getInstanceByRatio(r)
        }"
        @click.stop="emit('select-ratio', r)"
      >
        {{ r }}
      </button>
    </div>

    <!-- 3. 卡片底部操作按钮栏 -->
    <div class="set-card-btn-bar">
      <button
        type="button"
        class="btn-icon edit-btn"
        title="修改套件基础信息"
        @click.stop="emit('open-edit', set)"
      >
        ✏️
      </button>
      <button
        type="button"
        class="btn-icon upload-btn"
        :title="`上传/裁剪当前比例(${activeRatio})底图`"
        @click.stop="emit('open-upload', set, activeRatio)"
      >
        📤
      </button>
      <button
        type="button"
        class="btn-icon btn-status-toggle"
        :class="{ 'btn-enable': !set.is_active }"
        :title="set.is_active ? '停用此画布' : '启用此画布'"
        @click.stop="emit('toggle-active', $event, set)"
      >
        {{ set.is_active ? '⏸️' : '▶️' }}
      </button>
      <button
        v-if="isBuiltinSet"
        type="button"
        class="btn-icon del-btn disabled"
        disabled
        title="内置预设底图不可删除，但可以停用"
        style="opacity: 0.3; cursor: not-allowed;"
      >
        🗑️
      </button>
      <button
        v-else
        type="button"
        class="btn-icon del-btn"
        title="删除此画布套件"
        @click.stop="emit('delete', $event, set)"
      >
        🗑️
      </button>
    </div>
  </div>
</template>

<style scoped>
.set-detail-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  padding: 8px 8px 6px 8px;
  display: flex;
  flex-direction: column;
  cursor: grab;
  transition: all 0.2s;
  position: relative;
  height: 188px;
  justify-content: space-between;
  box-sizing: border-box;
}

.set-detail-card:active {
  cursor: grabbing;
}

.set-detail-card.over {
  border: 2px dashed #8b5cf6 !important;
  transform: scale(1.03);
}

.set-detail-card.grayscale-active .set-card-preview-box {
  opacity: 0.65;
  filter: grayscale(85%);
}

.set-detail-card:hover {
  border-color: #8b5cf6;
}

.set-detail-card.batch-selected {
  border-color: #ef4444 !important;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.4);
}

.batch-delete-checkbox-box {
  position: absolute;
  top: 6px;
  right: 6px;
  z-index: 10;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.set-card-preview-box {
  width: 100%;
  height: 110px;
  background-color: #121824;
  background-image: radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 0);
  background-size: 10px 10px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.05);
  position: relative;
}

.set-card-preview-img {
  max-width: 100%;
  max-height: 100%;
  height: 100%;
  object-fit: cover;
  cursor: zoom-in;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.set-card-empty-tip {
  font-size: 0.75rem;
  color: rgba(239, 68, 68, 0.6);
  font-weight: 700;
}

.set-card-title-banner {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.75) 0%, transparent 100%);
  padding: 8px 6px 4px 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 5;
}

.set-card-name-banner {
  font-size: 0.76rem;
  font-weight: 800;
  color: #ffffff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  text-align: left;
}

.set-card-price-banner {
  font-size: 0.65rem;
  background: rgba(16, 185, 129, 0.85);
  color: #ffffff;
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 800;
  margin-left: 6px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.ratio-switcher-row {
  display: flex;
  gap: 3px;
  width: 100%;
  margin: 3px 0 2px 0;
}

.btn-ratio-switch {
  flex: 1;
  font-size: 0.68rem;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--card-border);
  color: var(--text-muted);
  padding: 2px 0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.btn-ratio-switch:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-main);
}

.btn-ratio-switch.active {
  background: #8b5cf6;
  color: white;
  border-color: transparent;
}

.btn-ratio-switch.has-image::after {
  content: '';
  position: absolute;
  top: 2px;
  right: 2px;
  width: 4px;
  height: 4px;
  background: #10b981;
  border-radius: 50%;
}

.set-card-btn-bar {
  display: flex;
  gap: 5px;
  width: 100%;
  margin-top: 4px;
}

.set-card-btn-bar .btn-icon {
  flex: 1;
  height: 26px;
  font-size: 0.82rem;
  border-radius: 6px;
  border: 1px solid var(--card-border);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-main);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.set-card-btn-bar .btn-icon:hover {
  background: rgba(139, 92, 246, 0.12);
  border-color: #8b5cf6;
  transform: translateY(-1px);
}
</style>
