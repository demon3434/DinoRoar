<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'
import { BookOpen, Calendar, Smile, Frown, Meh, Sparkles } from 'lucide-vue-next'

interface DiaryItem {
  id: number
  title: string
  content: string
  mood: string
  user_id: number
  username?: string
  created_at: string
  stickers_count?: number
}

const diaries = ref<DiaryItem[]>([])
const loading = ref(false)
const selectedDiary = ref<DiaryItem | null>(null)

async function loadDiaries() {
  loading.value = true
  try {
    const res: any = await apiClient.get('/api/logs')
    diaries.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDiaries()
})
</script>

<template>
  <div class="diaries-view">
    <div class="action-bar glass-panel">
      <div>
        <h2 class="text-lg font-bold text-slate-100">心情日记看板</h2>
        <p class="text-xs text-slate-400">查看小朋友的每日情绪记录、手账贴纸与创作足迹</p>
      </div>
    </div>

    <div class="diaries-grid">
      <div v-if="loading" class="col-span-full loading-state glass-panel">
        <div class="spinner" />
        <span>正在加载日记记录...</span>
      </div>

      <div v-else-if="diaries.length === 0" class="col-span-full empty-state glass-panel">
        <BookOpen class="w-12 h-12 text-slate-500 mb-2" />
        <p>暂无日记记录</p>
      </div>

      <div
        v-for="d in diaries"
        :key="d.id"
        class="diary-card glass-panel glass-panel-hover"
        @click="selectedDiary = d"
      >
        <div class="card-header">
          <span class="mood-badge badge badge-info">
            <Smile class="w-3 h-3" />
            <span>{{ d.mood || '开心' }}</span>
          </span>
          <span class="date-tag font-mono">{{ d.created_at?.slice(0, 10) }}</span>
        </div>

        <h3 class="diary-title">{{ d.title || '今日手账' }}</h3>
        <p class="diary-snippet line-clamp-3">{{ d.content }}</p>

        <div class="card-footer">
          <span class="author-tag">作者 ID: #{{ d.user_id }}</span>
          <span v-if="d.stickers_count" class="stickers-tag">
            <Sparkles class="w-3 h-3 text-amber-400" />
            <span>{{ d.stickers_count }} 贴纸</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Diary Detail Modal -->
    <Teleport to="body">
      <div v-if="selectedDiary" class="modal-backdrop" @click="selectedDiary = null">
        <div class="modal-card animate-fade-in" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ selectedDiary.title || '日记详情' }}</h3>
            <span class="text-xs text-slate-400 font-mono">{{ selectedDiary.created_at }}</span>
          </div>
          <div class="modal-body">
            <p class="diary-full-content">{{ selectedDiary.content }}</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="selectedDiary = null">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.diaries-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  padding: 16px 20px;
}

.diaries-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.diary-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.date-tag {
  font-size: 0.76rem;
  color: var(--text-muted);
}

.diary-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 8px;
}

.diary-snippet {
  font-size: 0.88rem;
  color: var(--text-muted);
  line-height: 1.6;
  flex: 1;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.78rem;
  color: var(--text-subtle);
}

.stickers-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--accent-sunny);
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

.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: var(--modal-backdrop);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.modal-card {
  width: 100%;
  max-width: 560px;
  background: var(--modal-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.modal-body {
  padding: 20px 24px;
}

.diary-full-content {
  font-size: 0.95rem;
  line-height: 1.7;
  color: var(--text-main);
  white-space: pre-wrap;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: flex-end;
}
</style>
