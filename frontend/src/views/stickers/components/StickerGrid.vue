<script setup lang="ts">
import type { StickerItem } from '@/types/sticker'
import { Edit2, Trash2, Zap } from 'lucide-vue-next'

defineProps<{
  stickers: StickerItem[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', item: StickerItem): void
  (e: 'delete', item: StickerItem): void
  (e: 'toggleActive', item: StickerItem): void
}>()
</script>

<template>
  <div v-if="loading" class="loading-state glass-panel">
    <div class="spinner" />
    <span>正在加载贴纸资产...</span>
  </div>

  <div v-else-if="stickers.length === 0" class="empty-state glass-panel">
    <Zap class="w-10 h-10 text-amber-400 opacity-60 mb-2" />
    <p>未找到符合条件的贴纸资产</p>
  </div>

  <div v-else class="sticker-grid">
    <div
      v-for="item in stickers"
      :key="item.id"
      class="sticker-card glass-panel glass-panel-hover"
      :class="{ 'is-disabled': !item.is_active }"
    >
      <!-- Image Preview Area -->
      <div class="img-preview-box">
        <img :src="item.image_url" :alt="item.name" class="sticker-img" loading="lazy" />
        <span class="category-tag">{{ item.category }}</span>
      </div>

      <!-- Info & Actions -->
      <div class="card-footer">
        <div class="info-meta">
          <h4 class="sticker-name" :title="item.name">{{ item.name }}</h4>
          <span class="price-tag">{{ item.price || 0 }} 蛋能量</span>
        </div>

        <div class="card-actions">
          <button
            type="button"
            class="action-btn"
            title="编辑贴纸"
            @click="emit('edit', item)"
          >
            <Edit2 class="w-4 h-4 text-blue-400" />
          </button>
          <button
            type="button"
            class="action-btn"
            title="删除贴纸"
            @click="emit('delete', item)"
          >
            <Trash2 class="w-4 h-4 text-rose-400" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sticker-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 20px;
}

.sticker-card {
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-md);
  overflow: hidden;
  padding: 12px;
}

.sticker-card.is-disabled {
  opacity: 0.55;
  filter: grayscale(0.4);
}

.img-preview-box {
  width: 100%;
  aspect-ratio: 1;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 10px;
}

.sticker-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.25s ease;
}

.sticker-card:hover .sticker-img {
  transform: scale(1.08);
}

.category-tag {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(4px);
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 0.7rem;
  color: var(--text-muted);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card-footer {
  margin-top: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.info-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.sticker-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price-tag {
  font-size: 0.75rem;
  color: var(--accent-sunny);
  font-weight: 500;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--text-muted);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
