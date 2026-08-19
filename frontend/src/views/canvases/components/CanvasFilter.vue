<script setup lang="ts">
import { Search, Plus, Download, Upload } from 'lucide-vue-next'

defineProps<{
  searchKeyword: string
}>()

const emit = defineEmits<{
  (e: 'update:searchKeyword', val: string): void
  (e: 'create'): void
  (e: 'exportAll'): void
  (e: 'import'): void
}>()
</script>

<template>
  <div class="filter-bar glass-panel">
    <div class="search-box">
      <Search class="search-icon" />
      <input
        :value="searchKeyword"
        type="text"
        class="form-input search-input"
        placeholder="搜索画布套件名称..."
        @input="emit('update:searchKeyword', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="btn-group">
      <button type="button" class="btn btn-secondary" @click="emit('exportAll')">
        <Download class="w-4 h-4" />
        <span>导出全部</span>
      </button>
      <button type="button" class="btn btn-secondary" @click="emit('import')">
        <Upload class="w-4 h-4" />
        <span>导入套件</span>
      </button>
      <button type="button" class="btn btn-primary" @click="emit('create')">
        <Plus class="w-4 h-4" />
        <span>新建画布套件</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.search-box {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--text-muted);
}

.search-input {
  padding-left: 36px;
}

.btn-group {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
