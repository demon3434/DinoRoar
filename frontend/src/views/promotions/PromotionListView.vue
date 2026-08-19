<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PromotionItem } from '@/types/promotion'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import PromotionFormModal from './components/PromotionFormModal.vue'
import PromotionTable from './components/PromotionTable.vue'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const promotions = ref<PromotionItem[]>([])
const loading = ref(false)

// 筛选字段
const filterStatus = ref('')
const filterKeyword = ref('')
const filterStartDate = ref('')
const filterEndDate = ref('')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)
const totalPages = ref(1)

const isFormModalOpen = ref(false)
const isDeleteModalOpen = ref(false)
const selectedPromotion = ref<PromotionItem | null>(null)

// 字典数据
const stickerSeriesList = ref<any[]>([])
const canvasSeriesList = ref<any[]>([])

async function loadMetadata() {
  try {
    const [stRes, cvRes] = await Promise.all([
      apiClient.get('/api/stickers/config?for_admin=true').catch(() => []),
      apiClient.get('/api/canvases/config?for_admin=true').catch(() => [])
    ])
    stickerSeriesList.value = (stRes as any) || []
    canvasSeriesList.value = (cvRes as any) || []
  } catch (e) {}
}

async function loadData(page = 1) {
  currentPage.value = page
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      page_size: String(pageSize.value)
    })
    if (filterKeyword.value.trim()) params.append('keyword', filterKeyword.value.trim())
    if (filterStatus.value) params.append('status', filterStatus.value)
    if (filterStartDate.value) params.append('start_date', filterStartDate.value)
    if (filterEndDate.value) params.append('end_date', filterEndDate.value)

    const res: any = await apiClient.get(`/api/admin/promotions?${params.toString()}`)
    promotions.value = res.items || []
    totalCount.value = res.total || 0
    totalPages.value = res.total_pages || 1
  } catch (e) {
  } finally {
    loading.value = false
  }
}

function handleOpenCreate() {
  selectedPromotion.value = null
  isFormModalOpen.value = true
}

function handleOpenEdit(item: PromotionItem) {
  selectedPromotion.value = item
  isFormModalOpen.value = true
}

function handleOpenDelete(item: PromotionItem) {
  selectedPromotion.value = item
  isDeleteModalOpen.value = true
}

async function handleSavePromotion(data: Partial<PromotionItem>) {
  try {
    if (selectedPromotion.value) {
      await apiClient.put(`/api/admin/promotions/${selectedPromotion.value.id}`, data)
      showToast('优惠活动更新成功！', 'success')
    } else {
      await apiClient.post('/api/admin/promotions', data)
      showToast('优惠活动创建成功！', 'success')
    }
    isFormModalOpen.value = false
    loadData(currentPage.value)
  } catch (e) {}
}

async function handleDeleteConfirm() {
  if (!selectedPromotion.value) return
  try {
    await apiClient.delete(`/api/admin/promotions/${selectedPromotion.value.id}`)
    showToast('优惠活动已删除', 'success')
    isDeleteModalOpen.value = false
    loadData(currentPage.value)
  } catch (e) {}
}

async function handleToggleStatus(item: PromotionItem) {
  try {
    const res: any = await apiClient.patch(`/api/admin/promotions/${item.id}/toggle-active`, {
      is_active: !item.is_active
    })
    item.is_active = res.is_active
    showToast(item.is_active ? '活动已启用' : '活动已停用', 'success')
  } catch (err: any) {
    showToast(err.response?.data?.detail || '切换状态失败', 'error')
  }
}

function handleApplyFilter() {
  loadData(1)
}

function handleResetFilter() {
  filterStatus.value = ''
  filterKeyword.value = ''
  filterStartDate.value = ''
  filterEndDate.value = ''
  loadData(1)
}

function handleChangePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  loadData(page)
}

function handleChangePageSize(size: number) {
  pageSize.value = size
  loadData(1)
}

onMounted(() => {
  loadMetadata()
  loadData()
})
</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 6px;">
    <!-- 顶部标题与操作栏 (严格对齐 194 原版) -->
    <div class="promo-page-header">
      <div>
        <h2 style="font-size: 1.4rem; font-weight: 800; color: var(--text-main); margin: 0 0 4px 0; display: flex; align-items: center; gap: 8px;">
          🎉 优惠活动管理
        </h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">
          配置手账商城的限时特惠活动，支持全场通用折扣、分类/系列折扣及单品一口价
        </p>
      </div>
      <button class="btn btn-primary-purple" style="height: 38px; padding: 0 16px; font-weight: 700; white-space: nowrap;" @click="handleOpenCreate">
        <span>➕</span> 创建新优惠活动
      </button>
    </div>

    <!-- 顶部筛选工具栏 (纯单行横向排开) -->
    <div class="promo-filter-card">
      <div class="filter-item" style="min-width: 180px; max-width: 240px; flex: 1;">
        <input
          v-model="filterKeyword"
          type="text"
          class="form-control"
          placeholder="🔍 搜索活动名称或文案..."
          style="height: 32px; font-size: 0.82rem; padding: 4px 10px;"
          @keydown.enter="handleApplyFilter"
        />
      </div>

      <div class="filter-item">
        <span class="filter-label">状态:</span>
        <select v-model="filterStatus" class="form-control" style="width: 105px; height: 32px; font-size: 0.82rem; padding: 4px 8px; border-radius: 8px;" @change="handleApplyFilter">
          <option value="">全部状态</option>
          <option value="active">🟢 进行中</option>
          <option value="upcoming">🟡 未开始</option>
          <option value="ended">⚪ 已结束</option>
          <option value="disabled">🔴 已停用</option>
        </select>
      </div>

      <div class="filter-item">
        <span class="filter-label">日期:</span>
        <div class="filter-date-group">
          <input v-model="filterStartDate" type="date" title="开始日期" @change="handleApplyFilter" />
          <span style="color: var(--text-muted); font-size: 0.78rem; padding: 0 2px;">至</span>
          <input v-model="filterEndDate" type="date" title="截止日期" @change="handleApplyFilter" />
        </div>
      </div>

      <div class="filter-btn-group">
        <button type="button" class="btn btn-primary-purple" style="height: 32px; padding: 0 14px; font-size: 0.82rem; font-weight: 700;" @click="handleApplyFilter">
          🔍 查询
        </button>
        <button type="button" class="btn-outline-purple" style="height: 32px; padding: 0 12px; font-size: 0.82rem;" @click="handleResetFilter">
          ↺ 重置
        </button>
      </div>
    </div>

    <!-- 表格组件 (含底部完整分页信息) -->
    <PromotionTable
      :promotions="promotions"
      :loading="loading"
      :total-count="totalCount"
      :current-page="currentPage"
      :total-pages="totalPages"
      :page-size="pageSize"
      :sticker-series-list="stickerSeriesList"
      :canvas-series-list="canvasSeriesList"
      @edit="handleOpenEdit"
      @delete="handleOpenDelete"
      @toggle-status="handleToggleStatus"
      @create="handleOpenCreate"
      @change-page="handleChangePage"
      @change-page-size="handleChangePageSize"
    />

    <!-- 创建 / 编辑促销弹窗 -->
    <PromotionFormModal
      v-model="isFormModalOpen"
      :promotion-data="selectedPromotion"
      @save="handleSavePromotion"
    />

    <!-- 删除确认弹窗 -->
    <ConfirmModal
      v-model="isDeleteModalOpen"
      title="删除活动确认"
      :message="`确定要删除优惠活动「${selectedPromotion?.name}」吗？删除后正在进行的折扣将立即失效。`"
      confirm-text="确认删除"
      type="danger"
      @confirm="handleDeleteConfirm"
    />
  </div>
</template>

<style scoped>
.promo-page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.promo-filter-card {
  background: var(--card-bg, rgba(255, 255, 255, 0.8));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 14px;
  padding: 8px 14px;
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
  overflow-x: auto;
  flex-wrap: nowrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.filter-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
}

.filter-date-group {
  display: inline-flex;
  align-items: center;
  background: var(--input-bg, rgba(0, 0, 0, 0.03));
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.12));
  border-radius: 8px;
  padding: 0 6px;
  height: 32px;
}

.filter-date-group input[type="date"] {
  border: none;
  background: transparent;
  font-size: 0.8rem;
  color: var(--text-main);
  padding: 0 2px;
  outline: none;
  height: 100%;
}

.filter-btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}
</style>
