<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import ReceiptDrawer from './components/ReceiptDrawer.vue'

interface TransactionItem {
  id: number
  user_id: number
  username: string
  nickname: string | null
  event_type_id: number
  event_name: string
  change_amount: number
  balance_after: number
  target_type_id: number
  target_id: number
  request_uuid: string | null
  created_at: string
  month_group: string
  asset_display: {
    title: string
    subtitle?: string
    badge_label: string
    type_icon?: string
    image_url: string | null
    theme_color: string
    direction?: string
    detail_info: Record<string, any> | null
  }
}

interface UserOption {
  id: number
  username: string
  nickname: string | null
  egg_energy?: number
}

// 计算当前月份起止日期
function getCurrentMonthRange() {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const pad = (n: number) => String(n).padStart(2, '0')
  const firstDay = `${year}-${pad(month)}-01`
  const lastDayObj = new Date(year, month, 0)
  const lastDay = `${year}-${pad(month)}-${pad(lastDayObj.getDate())}`
  return { firstDay, lastDay }
}

const defaultRange = getCurrentMonthRange()

const loading = ref(false)
const transactions = ref<TransactionItem[]>([])
const users = ref<UserOption[]>([])

const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

// 筛选条件（默认当月）
const selectedUserId = ref<number | ''>('')
const selectedEventType = ref<number | ''>('')
const startDate = ref(defaultRange.firstDay)
const endDate = ref(defaultRange.lastDay)

// 抽屉详情
const selectedTx = ref<TransactionItem | null>(null)
const isDrawerOpen = ref(false)

// 当前选中的孩子计算属性（用于动态显示其蛋能量）
const currentSelectedUser = computed(() => {
  if (selectedUserId.value === '') return null
  return users.value.find((u) => u.id === selectedUserId.value) || null
})

// 总页数计算
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / pageSize.value))
})

// 获取事件类型的专属 Emoji 与标识
function getEventMeta(eventTypeId: number) {
  switch (eventTypeId) {
    case 101:
      return { icon: '🥚', label: '每日签到', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' }
    case 201:
      return { icon: '📖', label: '手账日记', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)' }
    case 301:
      return { icon: '🛒', label: '商城兑换', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' }
    case 401:
      return { icon: '🎁', label: '活动奖品', color: '#ec4899', bg: 'rgba(236, 72, 153, 0.12)' }
    default:
      return { icon: '⚡', label: '能量变动', color: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.12)' }
  }
}

async function fetchUsers() {
  try {
    const res: any = await apiClient.get('/api/admin/users')
    users.value = (res || []).filter((u: any) => !u.is_admin)
  } catch (e: any) {
    console.error('加载用户列表失败', e)
  }
}

async function fetchTransactions() {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value
    }
    if (selectedUserId.value !== '') params.user_id = selectedUserId.value
    if (selectedEventType.value !== '') params.event_type_id = selectedEventType.value
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value

    const res: any = await apiClient.get('/api/admin/energy/transactions', { params })
    transactions.value = res.items || []
    total.value = res.total || 0
  } catch (e: any) {
    showToast(e.response?.data?.detail || '获取流水账本失败', 'error')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchTransactions()
}

function handleReset() {
  selectedUserId.value = ''
  selectedEventType.value = ''
  const range = getCurrentMonthRange()
  startDate.value = range.firstDay
  endDate.value = range.lastDay
  page.value = 1
  fetchTransactions()
}

function handlePageSizeChange(newSize: number) {
  pageSize.value = newSize
  page.value = 1
  fetchTransactions()
}

function openReceipt(tx: TransactionItem) {
  selectedTx.value = tx
  isDrawerOpen.value = true
}

onMounted(() => {
  fetchUsers()
  fetchTransactions()
})
</script>

<template>
  <div style="display: flex; flex-direction: column; width: 100%; gap: 16px;">
    <!-- 顶部 Header (严格对齐全局风格) -->
    <header class="page-header">
      <div>
        <h2 class="page-title">
          <span>🥚</span> 蛋能量流水账本
        </h2>
      </div>
      <button class="btn btn-outline-purple" @click="fetchTransactions" :disabled="loading">
        <span :class="{ spinning: loading }">🔄</span> 刷新对账
      </button>
    </header>

    <!-- 顶部筛选工具栏 (纯单行横向排开，适配当前主题配色) -->
    <div class="filter-card">
      <div class="filter-controls">
        <div class="filter-item">
          <span class="filter-label">孩子账户:</span>
          <select v-model="selectedUserId" class="filter-select" @change="handleSearch">
            <option value="">全部孩子</option>
            <option v-for="u in users" :key="u.id" :value="u.id">
              {{ u.nickname ? `${u.nickname} (@${u.username})` : u.username }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <span class="filter-label">事件分类:</span>
          <select v-model="selectedEventType" class="filter-select" @change="handleSearch">
            <option value="">全部分类</option>
            <option :value="101">🥚 每日签到奖励</option>
            <option :value="201">📖 手账日记奖励</option>
            <option :value="301">🛒 商城资产兑换</option>
            <option :value="401">🎁 活动神秘奖品</option>
          </select>
        </div>

        <div class="filter-item">
          <span class="filter-label">日期区间:</span>
          <div class="filter-date-group">
            <input v-model="startDate" type="date" title="开始日期" @change="handleSearch" />
            <span class="date-sep">至</span>
            <input v-model="endDate" type="date" title="截止日期" @change="handleSearch" />
          </div>
        </div>

        <div class="filter-btn-group">
          <button type="button" class="btn btn-primary-purple btn-action" @click="handleSearch">
            🔍 筛选
          </button>
          <button type="button" class="btn-outline-purple btn-action" @click="handleReset">
            ↺ 重置
          </button>
        </div>
      </div>

      <!-- 选中孩子时动态展示其实时持有蛋能量 -->
      <div v-if="currentSelectedUser" class="child-energy-badge">
        <span class="badge-icon">🥚</span>
        <span class="badge-text">
          「{{ currentSelectedUser.nickname || currentSelectedUser.username }}」当前持有蛋能量：
          <strong>{{ (currentSelectedUser.egg_energy ?? 0).toLocaleString() }}</strong>
        </span>
      </div>
    </div>

    <!-- 资金对账明细卡片表格 (跟随主题自适应配色) -->
    <div class="ledger-table-card">
      <table class="ledger-table">
        <thead>
          <tr>
            <th style="width: 170px;">交易时间</th>
            <th style="width: 140px;">孩子账户</th>
            <th style="width: 120px; text-align: center;">事件类型</th>
            <th>关联合同实体 / 详情说明</th>
            <th style="width: 120px; text-align: center;">变动能量</th>
            <th style="width: 110px; text-align: center;">变动后余额</th>
            <th style="width: 90px; text-align: center;">电子回单</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading && transactions.length === 0">
            <td colspan="7" class="empty-cell">
              数据加载中...
            </td>
          </tr>
          <tr v-else-if="transactions.length === 0">
            <td colspan="7" class="empty-cell">
              暂无符合条件的交易对账记录
            </td>
          </tr>
          <tr
            v-for="tx in transactions"
            :key="tx.id"
            class="tx-row"
            @click="openReceipt(tx)"
          >
            <!-- 交易时间 -->
            <td class="col-time font-mono">
              {{ tx.created_at }}
            </td>

            <!-- 孩子账户 -->
            <td>
              <div class="user-chip">
                <span class="chip-avatar">🦖</span>
                <span class="chip-name">{{ tx.nickname || tx.username }}</span>
              </div>
            </td>

            <!-- 事件类型 -->
            <td style="text-align: center;">
              <span
                class="event-badge"
                :style="{
                  color: getEventMeta(tx.event_type_id).color,
                  backgroundColor: getEventMeta(tx.event_type_id).bg,
                  borderColor: getEventMeta(tx.event_type_id).color
                }"
              >
                {{ getEventMeta(tx.event_type_id).icon }} {{ getEventMeta(tx.event_type_id).label }}
              </span>
            </td>

            <!-- 关联合同实体 / 物化图鉴 / 详情说明 -->
            <td>
              <div class="asset-cell">
                <div
                  v-if="tx.asset_display.image_url"
                  class="thumb-wrap"
                >
                  <img
                    :src="tx.asset_display.image_url"
                    class="asset-thumb"
                    @error="(e) => ((e.target as HTMLElement).style.display = 'none')"
                  />
                </div>
                <div class="asset-info">
                  <div class="asset-title">
                    {{ tx.asset_display.title }}
                  </div>
                  <div v-if="tx.asset_display.subtitle" class="asset-subtitle">
                    {{ tx.asset_display.subtitle }}
                  </div>
                  <div v-if="tx.request_uuid" class="asset-uuid font-mono">
                    单号: {{ tx.request_uuid.slice(0, 10) }}...
                  </div>
                </div>
              </div>
            </td>

            <!-- 变动能量 -->
            <td style="text-align: center;">
              <span
                class="amount-pill font-mono"
                :class="tx.change_amount > 0 ? 'text-emerald' : 'text-amber'"
              >
                {{ tx.change_amount > 0 ? '+' : '' }}{{ tx.change_amount }} 🥚
              </span>
            </td>

            <!-- 变动后余额 -->
            <td style="text-align: center;">
              <span class="balance-text font-mono">
                {{ tx.balance_after }}
              </span>
            </td>

            <!-- 电子回单按钮 -->
            <td style="text-align: center;" @click.stop="openReceipt(tx)">
              <button type="button" class="btn-sm btn-sm-primary btn-receipt">
                🧾 回单
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 表格底部工具栏 (含每页条数选择器与翻页) -->
      <div class="table-footer">
        <div class="footer-left">
          <span>共 <strong style="color: var(--text-main);">{{ total }}</strong> 笔交易明细</span>
          <span class="footer-divider">|</span>
          <label class="page-size-label">
            <span>每页显示</span>
            <select
              :value="pageSize"
              class="page-size-select"
              @change="handlePageSizeChange(Number(($event.target as HTMLSelectElement).value))"
            >
              <option :value="10">10 笔</option>
              <option :value="20">20 笔</option>
              <option :value="50">50 笔</option>
              <option :value="100">100 笔</option>
            </select>
          </label>
        </div>

        <div class="footer-right">
          <button
            type="button"
            class="btn-sm"
            :disabled="page <= 1"
            :style="page <= 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''"
            @click="page--; fetchTransactions()"
          >
            上一页
          </button>
          <span class="page-count-text">{{ page }} / {{ totalPages }}</span>
          <button
            type="button"
            class="btn-sm"
            :disabled="page >= totalPages"
            :style="page >= totalPages ? 'opacity: 0.5; cursor: not-allowed;' : ''"
            @click="page++; fetchTransactions()"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- 侧边拟物电子回单抽屉组件 -->
    <ReceiptDrawer
      v-model="isDrawerOpen"
      :tx="selectedTx"
    />
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  width: 100%;
}

.page-title {
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 筛选工具栏 (对齐全局卡片与浅色/深色主题) */
.filter-card {
  background: var(--card-bg, rgba(255, 255, 255, 0.85));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 14px;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
}

.filter-select {
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.12));
  color: var(--text-main);
  border-radius: 8px;
  padding: 4px 8px;
  height: 32px;
  font-size: 0.82rem;
  outline: none;
  cursor: pointer;
}

.filter-date-group {
  display: inline-flex;
  align-items: center;
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
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

.date-sep {
  color: var(--text-muted, #94a3b8);
  font-size: 0.78rem;
  padding: 0 2px;
}

.filter-btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.btn-action {
  height: 32px;
  padding: 0 14px;
  font-size: 0.82rem;
  font-weight: 700;
  white-space: nowrap;
}

/* 选中孩子时的能量胶囊 */
.child-energy-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.3);
  color: #d97706;
  border-radius: 8px;
  padding: 5px 12px;
  font-size: 0.82rem;
  font-weight: 600;
  align-self: flex-start;
  animation: fadeIn 0.2s ease-out;
}

.child-energy-badge strong {
  font-size: 0.92rem;
  color: #b45309;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 表格卡片容器 (自适应浅色与深色主题) */
.ledger-table-card {
  background: var(--card-bg, rgba(255, 255, 255, 0.85));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.ledger-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
}

.ledger-table th {
  background: rgba(0, 0, 0, 0.03);
  padding: 14px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #64748b);
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  text-align: left;
  letter-spacing: 0.5px;
}

.ledger-table td {
  padding: 14px 18px;
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.05));
  font-size: 0.86rem;
  color: var(--text-main);
  vertical-align: middle;
}

.tx-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.tx-row:hover td {
  background: rgba(139, 92, 246, 0.03);
}

.col-time {
  color: var(--text-muted, #64748b);
  font-size: 0.82rem;
  white-space: nowrap;
}

.user-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  padding: 3px 8px;
  border-radius: 6px;
}

.chip-avatar {
  font-size: 0.95rem;
}

.chip-name {
  font-weight: 600;
  color: var(--text-main);
  font-size: 0.82rem;
}

.event-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.76rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid;
  white-space: nowrap;
}

.asset-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.thumb-wrap {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
}

.asset-thumb {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.asset-title {
  font-weight: 700;
  color: var(--text-main);
  font-size: 0.84rem;
}

.asset-subtitle {
  font-size: 0.76rem;
  color: var(--text-muted, #64748b);
}

.asset-uuid {
  font-size: 0.72rem;
  color: var(--text-muted, #94a3b8);
}

.amount-pill {
  font-weight: 800;
  font-size: 0.88rem;
  white-space: nowrap;
}

.balance-text {
  font-weight: 700;
  color: var(--text-main);
  font-size: 0.88rem;
}

.btn-receipt {
  padding: 3px 10px;
  font-size: 0.76rem;
  white-space: nowrap;
}

.font-mono {
  font-family: monospace;
}

.text-emerald {
  color: #10b981;
}

.text-amber {
  color: #f59e0b;
}

.empty-cell {
  text-align: center;
  padding: 40px;
  color: var(--text-muted, #64748b);
}

/* 表格底部工具栏 */
.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  font-size: 0.85rem;
  color: var(--text-muted, #64748b);
  flex-wrap: wrap;
  gap: 12px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.footer-divider {
  color: var(--card-border, rgba(0, 0, 0, 0.15));
}

.page-size-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
}

.page-size-select {
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.12));
  color: var(--text-main);
  border-radius: 6px;
  padding: 2px 6px;
  height: 28px;
  font-size: 0.82rem;
  outline: none;
  cursor: pointer;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-count-text {
  font-weight: 700;
  color: var(--text-main);
  padding: 0 4px;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}
</style>
