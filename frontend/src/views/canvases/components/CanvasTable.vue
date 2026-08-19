<script setup lang="ts">
import type { CanvasSet } from '@/types/canvas'
import { Edit2, Trash2, Download, Image as ImageIcon } from 'lucide-vue-next'

defineProps<{
  canvases: CanvasSet[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'edit', item: CanvasSet): void
  (e: 'delete', item: CanvasSet): void
  (e: 'export', item: CanvasSet): void
  (e: 'toggleActive', item: CanvasSet): void
}>()
</script>

<template>
  <div class="table-container glass-panel">
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <span>正在加载画布套件...</span>
    </div>

    <div v-else-if="canvases.length === 0" class="empty-state">
      <ImageIcon class="w-12 h-12 text-slate-500 mb-2" />
      <p>暂无画布套件数据</p>
    </div>

    <table v-else class="custom-table">
      <thead>
        <tr>
          <th>封面预览</th>
          <th>套件名称与描述</th>
          <th>包含比例实例</th>
          <th>售价 (蛋能量)</th>
          <th>排序权重</th>
          <th>状态</th>
          <th style="text-align: right;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in canvases" :key="item.id">
          <!-- Preview -->
          <td style="width: 80px;">
            <div class="cover-box">
              <img :src="item.preview_image_url" :alt="item.name" class="cover-img" />
            </div>
          </td>

          <!-- Name & Desc -->
          <td>
            <div class="name-box">
              <span class="font-bold text-slate-100">{{ item.name }}</span>
              <span class="text-xs text-slate-400 line-clamp-1">{{ item.description || '无详细描述' }}</span>
            </div>
          </td>

          <!-- Instances badge -->
          <td>
            <div class="ratio-badges">
              <span
                v-for="inst in item.instances || []"
                :key="inst.ratio_name"
                class="badge badge-info"
              >
                {{ inst.ratio_name }}
              </span>
              <span v-if="!item.instances?.length" class="text-xs text-slate-500">未配置</span>
            </div>
          </td>

          <!-- Price -->
          <td>
            <span class="text-amber-400 font-semibold">{{ item.price || 0 }} 蛋能量</span>
          </td>

          <!-- Sort Order -->
          <td>
            <span class="text-slate-300 font-mono">{{ item.sort_order }}</span>
          </td>

          <!-- Status Toggle -->
          <td>
            <button
              type="button"
              class="badge"
              :class="item.is_active ? 'badge-success' : 'badge-danger'"
              @click="emit('toggleActive', item)"
            >
              {{ item.is_active ? '已启用' : '已禁用' }}
            </button>
          </td>

          <!-- Actions -->
          <td style="text-align: right;">
            <div class="action-btns">
              <button
                type="button"
                class="action-btn"
                title="导出此套件"
                @click="emit('export', item)"
              >
                <Download class="w-4 h-4 text-emerald-400" />
              </button>
              <button
                type="button"
                class="action-btn"
                title="编辑套件"
                @click="emit('edit', item)"
              >
                <Edit2 class="w-4 h-4 text-blue-400" />
              </button>
              <button
                type="button"
                class="action-btn"
                title="删除套件"
                @click="emit('delete', item)"
              >
                <Trash2 class="w-4 h-4 text-rose-400" />
              </button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-container {
  overflow-x: auto;
  border-radius: var(--radius-lg);
}

.cover-box {
  width: 54px;
  height: 54px;
  border-radius: var(--radius-sm);
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.cover-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.name-box {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ratio-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
}

.action-btn {
  width: 30px;
  height: 30px;
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
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 56px;
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
