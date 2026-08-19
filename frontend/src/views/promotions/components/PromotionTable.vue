<script setup lang="ts">
import type { PromotionItem } from '@/types/promotion'

const props = defineProps<{
  promotions: PromotionItem[]
  loading: boolean
  totalCount: number
  currentPage: number
  totalPages: number
  pageSize: number
  stickerSeriesList: any[]
  canvasSeriesList: any[]
}>()

const emit = defineEmits<{
  (e: 'edit', item: PromotionItem): void
  (e: 'delete', item: PromotionItem): void
  (e: 'toggle-status', item: PromotionItem): void
  (e: 'create'): void
  (e: 'change-page', page: number): void
  (e: 'change-page-size', size: number): void
}>()

function getPromoStatus(item: PromotionItem) {
  if (!item.is_active) {
    return { label: '已停用', icon: '🔴', class: 'disabled' }
  }
  const now = new Date()
  const start = new Date(item.start_time)
  const end = new Date(item.end_time)

  if (now < start) {
    return { label: '未开始', icon: '🟡', class: 'upcoming' }
  }
  if (now > end) {
    return { label: '已结束', icon: '⚪', class: 'ended' }
  }
  return { label: '进行中', icon: '🟢', class: 'active' }
}

function formatDateTime(dtStr: string) {
  if (!dtStr) return '--'
  try {
    const d = new Date(dtStr)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  } catch {
    return dtStr
  }
}

function getSeriesName(seriesType: string, seriesId?: number): { name: string; typeLabel: string } {
  if (!seriesId) return { name: '', typeLabel: '' }
  const list = seriesType === 'CANVAS_SET' ? props.canvasSeriesList : props.stickerSeriesList
  let found = list.find((s) => Number(s.id) === Number(seriesId))
  let finalType = seriesType
  if (!found) {
    const altList = seriesType === 'CANVAS_SET' ? props.stickerSeriesList : props.canvasSeriesList
    found = altList.find((s) => Number(s.id) === Number(seriesId))
    if (found) finalType = seriesType === 'CANVAS_SET' ? 'STICKER' : 'CANVAS_SET'
  }
  const name = found ? found.name : `系列 #${seriesId}`
  const typeLabel = finalType === 'STICKER' ? '贴纸系列' : '画布系列'
  return { name, typeLabel }
}

function formatRuleSummary(targets: any[]) {
  if (!targets || targets.length === 0) return [{ scopeTxt: '无生效规则', discTxt: '' }]

  return targets.map((t) => {
    let scopeTxt = '🌟 全场所有商品'
    if (t.target_scope === 'ITEM_TYPE') {
      scopeTxt = t.target_type === 'CANVAS_SET' ? '🖼️ 所有背景画布' : '🎨 所有手账贴纸'
    } else if (t.target_scope === 'SERIES') {
      const sInfo = getSeriesName(t.target_type, t.target_id)
      scopeTxt = `📁 [${sInfo.typeLabel}] ${sInfo.name}`
    } else if (t.target_scope === 'SHOP_ITEM') {
      scopeTxt = `🛍️ [单品] ${t.target_name || `商品 #${t.target_id}`}`
    }

    let discTxt = ''
    if (t.fixed_price != null && t.fixed_price !== '') {
      discTxt = `一口价 ${t.fixed_price} 蛋能量`
    } else if (t.discount_rate != null) {
      discTxt = `全场 ${(t.discount_rate * 10).toFixed(1)} 折`
    }

    return { scopeTxt, discTxt }
  })
}
</script>

<template>
  <div class="promo-table-card">
    <div v-if="loading" style="text-align: center; padding: 60px 20px; color: var(--text-muted);">
      正在加载促销活动...
    </div>

    <div v-else-if="promotions.length === 0" style="text-align: center; padding: 60px 20px;">
      <div style="font-size: 2.5rem; margin-bottom: 12px;">🏷️</div>
      <div style="font-size: 1.1rem; font-weight: 800; color: var(--text-main); margin-bottom: 6px;">暂无促销活动</div>
      <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">点击右上角按钮即可一键配置节日打折或全场大促</div>
      <button class="btn btn-primary-purple" @click="emit('create')">创建第一个活动</button>
    </div>

    <div v-else>
      <table class="promo-table">
        <thead>
          <tr>
            <th style="text-align: left; width: 240px; min-width: 180px;">活动名称与文案</th>
            <th style="text-align: left; width: 185px; min-width: 180px; white-space: nowrap;">活动状态及时间</th>
            <th style="text-align: left;">优惠规则摘要</th>
            <th style="width: 75px; min-width: 75px; text-align: center; white-space: nowrap;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in promotions" :key="item.id">
            <td style="text-align: left;">
              <div style="font-weight: 800; color: var(--text-main); font-size: 0.95rem;">
                {{ item.name }}
              </div>
              <div v-if="item.description" style="font-size: 0.8rem; color: var(--text-muted); margin-top: 3px;">
                💬 {{ item.description }}
              </div>
            </td>

            <td style="text-align: left; line-height: 1.5; white-space: nowrap;">
              <div style="margin-bottom: 6px;">
                <span class="promo-badge" :class="getPromoStatus(item).class">
                  {{ getPromoStatus(item).icon }} {{ getPromoStatus(item).label }}
                </span>
              </div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">起: {{ formatDateTime(item.start_time) }}</div>
              <div style="font-size: 0.82rem; color: var(--text-muted);">止: {{ formatDateTime(item.end_time) }}</div>
            </td>

            <td style="text-align: left; font-size: 0.85rem; color: #7c3aed; font-weight: 600;">
              <div style="display: flex; flex-direction: column; gap: 4px;">
                <div v-for="(rule, rIdx) in formatRuleSummary(item.targets || (item as any).rules || [])" :key="rIdx" style="line-height: 1.4;">
                  <span style="color: #8b5cf6;">•</span> {{ rule.scopeTxt }} <span v-if="rule.discTxt">（<strong>{{ rule.discTxt }}</strong>）</span>
                </div>
              </div>
            </td>

            <td style="text-align: center; width: 75px; padding: 8px 6px;">
              <div style="display: flex; flex-direction: column; gap: 6px; align-items: center; justify-content: center;">
                <button
                  type="button"
                  class="btn-sm btn-sm-primary"
                  style="padding: 2px 0; font-size: 0.76rem; width: 54px; text-align: center; border-radius: 6px; font-weight: 700; background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.3);"
                  @click="emit('edit', item)"
                >
                  编辑
                </button>
                <div
                  class="capsule-switch"
                  :class="item.is_active ? 'active' : 'disabled'"
                  :title="item.is_active ? '点击停用活动' : '点击启用活动'"
                  @click="emit('toggle-status', item)"
                >
                  <span class="capsule-switch-dot"></span>
                  <span class="capsule-switch-text">{{ item.is_active ? '启用' : '停用' }}</span>
                </div>
                <button
                  type="button"
                  class="btn-sm btn-danger"
                  style="padding: 2px 0; font-size: 0.76rem; width: 54px; text-align: center; border-radius: 6px; font-weight: 700; background: #ef4444; color: #fff; border: 1px solid #ef4444;"
                  @click="emit('delete', item)"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 表格底部工具栏 -->
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 18px; border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.08)); font-size: 0.85rem; color: var(--text-muted); flex-wrap: wrap; gap: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span>共 <strong style="color: var(--text-main);">{{ totalCount }}</strong> 条促销活动</span>
          <span style="color: var(--card-border, rgba(0, 0, 0, 0.15));">|</span>
          <label style="display: inline-flex; align-items: center; gap: 6px;">
            <span>每页显示</span>
            <select
              :value="pageSize"
              class="form-control"
              style="width: auto; padding: 3px 8px; height: 30px; font-size: 0.82rem; border-radius: 6px; cursor: pointer;"
              @change="emit('change-page-size', Number(($event.target as HTMLSelectElement).value))"
            >
              <option :value="5">5 条</option>
              <option :value="10">10 条</option>
              <option :value="20">20 条</option>
              <option :value="50">50 条</option>
            </select>
          </label>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <button
            class="btn-sm"
            :disabled="currentPage <= 1"
            :style="currentPage <= 1 ? 'opacity: 0.5; cursor: not-allowed;' : ''"
            @click="emit('change-page', currentPage - 1)"
          >
            上一页
          </button>
          <span style="font-weight: 700; color: var(--text-main); padding: 0 4px;">{{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn-sm"
            :disabled="currentPage >= totalPages"
            :style="currentPage >= totalPages ? 'opacity: 0.5; cursor: not-allowed;' : ''"
            @click="emit('change-page', currentPage + 1)"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.promo-table-card {
  background: var(--card-bg, rgba(255, 255, 255, 0.8));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.promo-table {
  width: 100%;
  border-collapse: collapse;
}

.promo-table th {
  background: rgba(0, 0, 0, 0.03);
  padding: 14px 18px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-muted, #64748b);
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  letter-spacing: 0.5px;
}

.promo-table td {
  padding: 14px 18px;
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.05));
  font-size: 0.88rem;
  color: var(--text-main, #1e293b);
  vertical-align: middle;
}

.promo-table tr:hover td {
  background: rgba(139, 92, 246, 0.03);
}

.promo-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.promo-badge.active {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.promo-badge.upcoming {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.promo-badge.ended {
  background: rgba(156, 163, 175, 0.12);
  color: #6b7280;
  border: 1px solid rgba(156, 163, 175, 0.3);
}

.promo-badge.disabled {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* 现代文字滑动胶囊开关 (Capsule Switch) */
.capsule-switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 54px;
  height: 22px;
  border-radius: 11px;
  cursor: pointer;
  user-select: none;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-sizing: border-box;
}

.capsule-switch.active {
  background: #10b981;
  box-shadow: 0 1px 4px rgba(16, 185, 129, 0.35);
}

.capsule-switch.disabled {
  background: #94a3b8;
  box-shadow: 0 1px 4px rgba(148, 163, 184, 0.2);
}

.capsule-switch-dot {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: #ffffff;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.capsule-switch.active .capsule-switch-dot {
  transform: translateX(32px);
}

.capsule-switch.disabled .capsule-switch-dot {
  transform: translateX(0);
}

.capsule-switch-text {
  width: 100%;
  font-size: 0.68rem;
  font-weight: 800;
  color: #ffffff;
  line-height: 1;
  text-align: right;
  padding-right: 5px;
  letter-spacing: 0.5px;
}

.capsule-switch.active .capsule-switch-text {
  text-align: left;
  padding-left: 6px;
  padding-right: 0;
}
</style>
