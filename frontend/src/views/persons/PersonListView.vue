<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import ConfirmModal from '@/components/common/ConfirmModal.vue'
import { Plus, Trash2, UserCheck, Heart } from 'lucide-vue-next'

interface PersonItem {
  id: number
  name: string
  relation?: string
  avatar_url?: string
  color?: string
}

const persons = ref<PersonItem[]>([])
const loading = ref(false)

const isCreateModalOpen = ref(false)
const isDeleteModalOpen = ref(false)
const selectedPerson = ref<PersonItem | null>(null)

const newName = ref('')
const newRelation = ref('')

async function loadPersons() {
  loading.value = true
  try {
    const res: any = await apiClient.get('/api/persons')
    persons.value = res || []
  } catch (e) {
  } finally {
    loading.value = false
  }
}

async function handleCreatePerson() {
  if (!newName.value.trim()) return
  try {
    await apiClient.post('/api/persons', {
      name: newName.value.trim(),
      relation: newRelation.value.trim() || '朋友'
    })
    showToast('人物创建成功', 'success')
    isCreateModalOpen.value = false
    newName.value = ''
    newRelation.value = ''
    loadPersons()
  } catch (e) {}
}

async function handleDeletePerson() {
  if (!selectedPerson.value) return
  try {
    await apiClient.delete(`/api/persons/${selectedPerson.value.id}`)
    showToast('人物已删除', 'success')
    isDeleteModalOpen.value = false
    loadPersons()
  } catch (e) {}
}

onMounted(() => {
  loadPersons()
})
</script>

<template>
  <div class="persons-view">
    <div class="action-bar glass-panel">
      <div>
        <h2 class="text-lg font-bold text-slate-100">人物库管理</h2>
        <p class="text-xs text-slate-400">管理日记协同陪伴者（爸爸、妈妈、老师、小伙伴等）</p>
      </div>

      <button type="button" class="btn btn-primary" @click="isCreateModalOpen = true">
        <Plus class="w-4 h-4" />
        <span>添加人物</span>
      </button>
    </div>

    <div class="persons-grid">
      <div v-if="loading" class="col-span-full loading-state glass-panel">
        <div class="spinner" />
        <span>正在加载人物库...</span>
      </div>

      <div v-else-if="persons.length === 0" class="col-span-full empty-state glass-panel">
        <UserCheck class="w-12 h-12 text-slate-500 mb-2" />
        <p>暂无人物库记录</p>
      </div>

      <div
        v-for="p in persons"
        :key="p.id"
        class="person-card glass-panel glass-panel-hover"
      >
        <div class="person-avatar">
          <Heart class="w-6 h-6 text-rose-400" />
        </div>
        <div class="person-info">
          <h3 class="person-name">{{ p.name }}</h3>
          <span class="badge badge-info">{{ p.relation || '小伙伴' }}</span>
        </div>
        <button
          type="button"
          class="btn-del"
          title="删除人物"
          @click="selectedPerson = p; isDeleteModalOpen = true"
        >
          <Trash2 class="w-4 h-4 text-rose-400" />
        </button>
      </div>
    </div>

    <!-- Create Person Modal -->
    <Teleport to="body">
      <div v-if="isCreateModalOpen" class="modal-backdrop" @click="isCreateModalOpen = false">
        <div class="modal-card animate-fade-in" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">添加新人物</h3>
          </div>
          <form class="modal-body" @submit.prevent="handleCreatePerson">
            <div class="form-group">
              <label class="form-label">人物姓名/称呼</label>
              <input v-model="newName" type="text" class="form-input" placeholder="例如：乐乐" required />
            </div>
            <div class="form-group">
              <label class="form-label">与孩子关系</label>
              <input v-model="newRelation" type="text" class="form-input" placeholder="例如：同桌 / 朋友" />
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="isCreateModalOpen = false">取消</button>
              <button type="submit" class="btn btn-primary">添加</button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <ConfirmModal
      v-model="isDeleteModalOpen"
      title="删除人物确认"
      :message="`确定要从人物库删除「${selectedPerson?.name}」吗？`"
      confirm-text="确认删除"
      type="danger"
      @confirm="handleDeletePerson"
    />
  </div>
</template>

<style scoped>
.persons-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.action-bar {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.persons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.person-card {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.person-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(244, 63, 94, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  shrink: 0;
}

.person-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.person-name {
  font-size: 0.96rem;
  font-weight: 700;
  color: var(--text-main);
}

.btn-del {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: background 0.2s ease;
}

.btn-del:hover {
  background: rgba(239, 68, 68, 0.15);
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
  max-width: 420px;
  background: var(--modal-bg);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.modal-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-footer {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
