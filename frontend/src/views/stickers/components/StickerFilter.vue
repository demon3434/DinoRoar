<script setup lang="ts">
import { Search, Plus, Download, Upload } from 'lucide-vue-next'

defineProps<{
  categories: string[]
  activeCategory: string
  searchKeyword: string
}>()

const emit = defineEmits<{
  (e: 'update:activeCategory', val: string): void
  (e: 'update:searchKeyword', val: string): void
  (e: 'create'): void
  (e: 'export'): void
  (e: 'import'): void
}>()
</script>

<template>
  <div class="filter-bar card" style="padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; border: 1px solid var(--card-border);">
    <div class="top-row">
      <!-- 页面标题 -->
      <div>
        <h2 style="font-size: 1.3rem; font-weight: 800; color: var(--text-main); margin-bottom: 4px;">
          🦄 贴纸资产管理
        </h2>
        <p style="font-size: 0.8rem; color: var(--text-muted);">
          管理恐龙手账可用贴纸资产、分类与蛋能量兑换价格
        </p>
      </div>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <button type="button" class="btn btn-sm" @click="emit('import')">
          <Upload class="w-4 h-4" />
          <span>批量导入</span>
        </button>
        <button type="button" class="btn btn-sm" @click="emit('export')">
          <Download class="w-4 h-4" />
          <span>导出 ZIP</span>
        </button>
        <button type="button" class="btn btn-primary-purple btn-sm" @click="emit('create')">
          <Plus class="w-4 h-4" />
          <span>新建贴纸</span>
        </button>
      </div>
    </div>

    <div class="bottom-row">
      <!-- Category Tabs 药丸分类 -->
      <div class="category-tabs">
        <button
          type="button"
          class="cat-pill"
          :class="{ active: activeCategory === '' }"
          @click="emit('update:activeCategory', '')"
        >
          全部贴纸
        </button>
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          class="cat-pill"
          :class="{ active: activeCategory === cat }"
          @click="emit('update:activeCategory', cat)"
        >
          {{ cat }}
        </button>
      </div>

      <!-- 搜索框 -->
      <div class="search-box">
        <Search class="search-icon" />
        <input
          :value="searchKeyword"
          type="text"
          class="form-control search-input"
          placeholder="搜索贴纸名称..."
          @input="emit('update:searchKeyword', ($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.category-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.cat-pill {
  padding: 6px 14px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--card-border);
  color: var(--text-muted);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.cat-pill:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-main);
}

.cat-pill.active {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8b5cf6;
  color: #c084fc;
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
}

.search-box {
  position: relative;
  width: 240px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 15px;
  height: 15px;
  color: var(--text-muted);
}

.search-input {
  padding-left: 36px;
  height: 36px;
  font-size: 0.85rem;
}
</style>
