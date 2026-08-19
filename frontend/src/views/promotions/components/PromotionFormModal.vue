<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import type { PromotionItem, PromotionTarget } from '@/types/promotion'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'
import PromotionTargetPicker from './PromotionTargetPicker.vue'

const props = defineProps<{
  modelValue: boolean
  promotionData?: PromotionItem | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
  (e: 'save', data: Partial<PromotionItem>): void
}>()

interface RuleRow {
  id?: number
  target_scope: string // 'ALL' | 'ITEM_TYPE' | 'SERIES'
  target_type: string  // 'CANVAS_SET' | 'STICKER'
  target_id: number | null
  pricing_mode: string // 'DISCOUNT' | 'FIXED'
  discount_rate_display: string // e.g. '8.0'
  fixed_price: number | ''
}

const name = ref('')
const description = ref('')
const startTime = ref('')
const endTime = ref('')
const sortOrder = ref(1)
const rules = ref<RuleRow[]>([])

// 字典元数据
const availableStickerSeries = ref<any[]>([])
const availableCanvasSeries = ref<any[]>([])

// 系列选择器抽屉状态
const isPickerOpen = ref(false)
const activePickerRuleIdx = ref<number | null>(null)
const pickerType = ref<'STICKER' | 'CANVAS_SET'>('STICKER')
const selectedPickerSeriesId = ref<number | null>(null)

let mouseDownOnBackdrop = false

function onBackdropMouseDown(e: MouseEvent) {
  mouseDownOnBackdrop = e.target === e.currentTarget
}

function onBackdropClick(e: MouseEvent, closeFn: () => void) {
  if (mouseDownOnBackdrop && e.target === e.currentTarget) {
    closeFn()
  }
  mouseDownOnBackdrop = false
}

async function loadMetadata() {
  try {
    const [stRes, cvRes] = await Promise.all([
      apiClient.get('/api/stickers/config?for_admin=true').catch(() => []),
      apiClient.get('/api/canvases/config?for_admin=true').catch(() => [])
    ])
    availableStickerSeries.value = (stRes as any) || []
    availableCanvasSeries.value = (cvRes as any) || []
  } catch (e) {}
}

function toLocalDatetimeInputString(date: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

watch(
  () => props.promotionData,
  (val) => {
    if (val) {
      name.value = val.name
      description.value = val.description || ''
      startTime.value = val.start_time ? toLocalDatetimeInputString(new Date(val.start_time)) : ''
      endTime.value = val.end_time ? toLocalDatetimeInputString(new Date(val.end_time)) : ''
      sortOrder.value = val.sort_order || 1

      const srcTargets = val.targets || (val as any).rules || []
      if (srcTargets.length > 0) {
        rules.value = srcTargets.map((t: any) => {
          const scope = t.target_scope === 'SHOP_ITEM' ? 'SERIES' : (t.target_scope || 'ALL')
          const isFixed = t.fixed_price != null && t.fixed_price !== ''
          return {
            id: t.id,
            target_scope: scope,
            target_type: t.target_type || 'CANVAS_SET',
            target_id: t.target_id || null,
            pricing_mode: isFixed ? 'FIXED' : 'DISCOUNT',
            discount_rate_display: t.discount_rate != null ? (t.discount_rate * 10).toFixed(1) : '8.0',
            fixed_price: t.fixed_price != null ? t.fixed_price : ''
          }
        })
      } else {
        rules.value = [
          {
            target_scope: 'ALL',
            target_type: 'CANVAS_SET',
            target_id: null,
            pricing_mode: 'DISCOUNT',
            discount_rate_display: '8.0',
            fixed_price: ''
          }
        ]
      }
    } else {
      name.value = ''
      description.value = ''
      const now = new Date()
      const after7Days = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
      startTime.value = toLocalDatetimeInputString(now)
      endTime.value = toLocalDatetimeInputString(after7Days)
      sortOrder.value = 1
      rules.value = [
        {
          target_scope: 'ALL',
          target_type: 'CANVAS_SET',
          target_id: null,
          pricing_mode: 'DISCOUNT',
          discount_rate_display: '8.0',
          fixed_price: ''
        }
      ]
    }
  },
  { immediate: true }
)

function addRuleRow() {
  rules.value.push({
    target_scope: 'ALL',
    target_type: 'CANVAS_SET',
    target_id: null,
    pricing_mode: 'DISCOUNT',
    discount_rate_display: '8.0',
    fixed_price: ''
  })
}

function removeRuleRow(idx: number) {
  rules.value.splice(idx, 1)
}

function getSeriesInfo(seriesType: string, seriesId: number | null) {
  if (!seriesId) return null
  const list = seriesType === 'CANVAS_SET' ? availableCanvasSeries.value : availableStickerSeries.value
  let found = list.find((s) => Number(s.id) === Number(seriesId))
  let finalType = seriesType
  if (!found) {
    const altList = seriesType === 'CANVAS_SET' ? availableStickerSeries.value : availableCanvasSeries.value
    found = altList.find((s) => Number(s.id) === Number(seriesId))
    if (found) finalType = seriesType === 'CANVAS_SET' ? 'STICKER' : 'CANVAS_SET'
  }
  if (!found) return { name: `系列 #${seriesId}`, cover: '/static/images/ic_launcher.png' }

  let cover = ''
  if (finalType === 'STICKER') {
    cover = found.stickers?.[0]?.image_url || '/static/images/ic_launcher.png'
  } else {
    const firstSet = found.sets?.[0]
    cover = firstSet?.instances?.[0]?.image_url || firstSet?.image_url || '/static/images/default_canvases/default_canvas_16_9.png'
  }
  return { name: found.name, cover }
}

function openPickerModal(idx: number) {
  activePickerRuleIdx.value = idx
  const r = rules.value[idx]
  pickerType.value = (r.target_type as any) || 'STICKER'
  selectedPickerSeriesId.value = r.target_id
  isPickerOpen.value = true
}

function handlePickerSelect(seriesId: number, targetType: 'STICKER' | 'CANVAS_SET') {
  if (activePickerRuleIdx.value !== null) {
    const r = rules.value[activePickerRuleIdx.value]
    r.target_id = seriesId
    r.target_type = targetType
  }
}

function handleClose() {
  emit('update:modelValue', false)
}

function handleSubmit() {
  if (!name.value.trim()) {
    showToast('请输入活动名称', 'warning')
    return
  }
  if (!startTime.value || !endTime.value) {
    showToast('请设置活动起止时间', 'warning')
    return
  }

  const formattedTargets: PromotionTarget[] = rules.value.map((r) => {
    const isFixed = r.pricing_mode === 'FIXED'
    const rateVal = parseFloat(r.discount_rate_display)
    const rate = !isNaN(rateVal) ? Number((rateVal / 10).toFixed(4)) : 0.8
    const fixedVal = r.fixed_price !== '' ? Number(r.fixed_price) : undefined

    return {
      target_scope: r.target_scope,
      target_type: r.target_type,
      target_id: r.target_scope === 'SERIES' ? r.target_id : undefined,
      discount_rate: isFixed ? undefined : rate,
      fixed_price: isFixed ? fixedVal : undefined
    }
  })

  emit('save', {
    name: name.value.trim(),
    description: description.value.trim(),
    start_time: startTime.value,
    end_time: endTime.value,
    sort_order: Number(sortOrder.value) || 1,
    targets: formattedTargets
  })
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (!isPickerOpen.value && props.modelValue) {
      handleClose()
    }
  }
}

onMounted(() => {
  loadMetadata()
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <!-- 主弹窗：创建/编辑优惠活动 -->
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="modal"
      style="display: flex; z-index: 1000;"
      @mousedown="onBackdropMouseDown"
      @click="onBackdropClick($event, handleClose)"
    >
      <div class="modal-dialog-custom" style="max-width: 740px; width: 95%; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; padding: 20px 24px; box-sizing: border-box; border-radius: 18px;" @click.stop>
        <!-- 弹窗 Header -->
        <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; width: 100%; flex-shrink: 0; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--card-border);">
          <span style="font-weight: 800; font-size: 1.15rem; color: var(--text-main);">
            {{ promotionData ? '编辑优惠活动' : '创建优惠活动' }}
          </span>
          <span class="modal-close-icon" title="关闭" @click="handleClose">✕</span>
        </div>

        <div style="padding-right: 4px; overflow-y: auto; flex: 1;">
          <form style="display: flex; flex-direction: column; gap: 12px;" @submit.prevent="handleSubmit">
            <!-- 1. 活动名称 -->
            <div class="form-group" style="margin: 0;">
              <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.95rem; font-weight: 800; color: var(--text-main);">
                活动名称 <span style="color: #ef4444;">*</span> <span style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted);">(30字以内)</span>
              </label>
              <input v-model="name" type="text" class="form-control" maxlength="30" placeholder="例如：2026年暑假英语学习奖励活动" required style="height: 36px; font-size: 0.85rem; width: 100%;" />
            </div>

            <!-- 2. 活动文案说明 -->
            <div class="form-group" style="margin: 0;">
              <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.95rem; font-weight: 800; color: var(--text-main);">
                活动文案说明 <span style="font-size: 0.78rem; font-weight: 600; color: var(--text-muted);">(50字以内，商城顶部横幅展示，选填)</span>
              </label>
              <input v-model="description" type="text" class="form-control" maxlength="50" placeholder="例如：好好学习，天天向上" style="height: 36px; font-size: 0.85rem; width: 100%;" />
            </div>

            <!-- 3. 生效起止时间 (紧凑双列排列，去除非原版的权重顺序) -->
            <div style="display: flex; gap: 20px; align-items: flex-end; margin-bottom: 4px;">
              <div class="form-group" style="width: 220px; margin: 0;">
                <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.95rem; font-weight: 800; color: var(--text-main);">
                  生效开始时间 <span style="color: #ef4444;">*</span>
                </label>
                <input v-model="startTime" type="datetime-local" class="form-control" required style="height: 36px; font-size: 0.85rem;" />
              </div>
              <div class="form-group" style="width: 220px; margin: 0;">
                <label class="form-label" style="display: block; margin-bottom: 6px; font-size: 0.95rem; font-weight: 800; color: var(--text-main);">
                  生效结束时间 <span style="color: #ef4444;">*</span>
                </label>
                <input v-model="endTime" type="datetime-local" class="form-control" required style="height: 36px; font-size: 0.85rem;" />
              </div>
            </div>

            <!-- 4. 优惠规则配置区 -->
            <div style="margin-top: 8px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 0.95rem; font-weight: 800; color: var(--text-main);">优惠规则配置</span>
                <button
                  type="button"
                  class="btn-outline-purple"
                  style="padding: 4px 12px; font-size: 0.8rem; height: 30px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"
                  @click="addRuleRow"
                >
                  ➕ 添加一条规则
                </button>
              </div>

              <!-- 规则单行胶囊横条列表 -->
              <div style="display: flex; flex-direction: column; gap: 8px;">
                <div
                  v-for="(rule, idx) in rules"
                  :key="idx"
                  class="rule-item-box"
                  style="display: flex; align-items: center; gap: 8px; background: var(--bg-surface, rgba(0, 0, 0, 0.02)); border: 1px solid var(--card-border, rgba(0, 0, 0, 0.1)); border-radius: 10px; padding: 6px 10px; flex-wrap: nowrap;"
                >
                  <!-- 1. 作用范围 -->
                  <div style="width: 120px; flex-shrink: 0;">
                    <select
                      v-model="rule.target_scope"
                      class="form-control"
                      style="height: 34px; font-size: 0.82rem; padding: 4px 6px; border-radius: 6px;"
                      @change="rule.target_id = null"
                    >
                      <option value="ALL">🌟 全场通用</option>
                      <option value="ITEM_TYPE">📦 按商品大类</option>
                      <option value="SERIES">📁 指定单品</option>
                    </select>
                  </div>

                  <!-- 2. 目标对象动态区域 (185px) -->
                  <div style="width: 185px; flex-shrink: 0;">
                    <div
                      v-if="rule.target_scope === 'ALL'"
                      style="display: flex; align-items: center; height: 34px; font-size: 0.82rem; color: #10b981; font-weight: 700; padding-left: 2px;"
                    >
                      ✓ 全场所有商品
                    </div>

                    <div v-else-if="rule.target_scope === 'ITEM_TYPE'">
                      <select
                        v-model="rule.target_type"
                        class="form-control"
                        style="width: 100%; height: 34px; font-size: 0.82rem; padding: 4px 6px; border-radius: 6px;"
                      >
                        <option value="CANVAS_SET">🖼️ 所有背景画布</option>
                        <option value="STICKER">🎨 所有手账贴纸</option>
                      </select>
                    </div>

                    <div v-else-if="rule.target_scope === 'SERIES'">
                      <div v-if="!rule.target_id">
                        <button
                          type="button"
                          class="btn-outline-purple"
                          style="width: 100%; height: 34px; font-size: 0.8rem; justify-content: center; padding: 0 8px; border-radius: 6px;"
                          @click="openPickerModal(idx)"
                        >
                          📁 选择单品...
                        </button>
                      </div>
                      <div
                        v-else
                        style="display: flex; align-items: center; justify-content: space-between; background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 6px; padding: 2px 6px; height: 34px; box-sizing: border-box; gap: 6px;"
                      >
                        <div style="display: flex; align-items: center; gap: 6px; overflow: hidden; min-width: 0;">
                          <img
                            :src="getSeriesInfo(rule.target_type, rule.target_id)?.cover"
                            style="width: 24px; height: 24px; object-fit: cover; border-radius: 4px; background: rgba(255, 255, 255, 0.7); flex-shrink: 0;"
                            onerror="this.src='/static/images/ic_launcher.png'"
                          />
                          <span
                            style="font-size: 0.8rem; font-weight: 700; color: var(--text-main); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"
                            :title="getSeriesInfo(rule.target_type, rule.target_id)?.name"
                          >
                            {{ getSeriesInfo(rule.target_type, rule.target_id)?.name }}
                          </span>
                        </div>
                        <button
                          type="button"
                          class="btn-sm btn-sm-primary"
                          style="padding: 2px 7px; font-size: 0.74rem; height: 24px; flex-shrink: 0; white-space: nowrap; line-height: 1; border-radius: 5px;"
                          @click="openPickerModal(idx)"
                        >
                          更换单品
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- 3. 优惠定价方式 -->
                  <div style="width: 125px; flex-shrink: 0;">
                    <select
                      v-model="rule.pricing_mode"
                      class="form-control"
                      style="height: 34px; font-size: 0.82rem; padding: 4px 6px; border-radius: 6px;"
                    >
                      <option value="DISCOUNT">🏷️ 折扣率打折</option>
                      <option value="FIXED">🎯 一口价特惠</option>
                    </select>
                  </div>

                  <!-- 4. 数值输入框 (110px) -->
                  <div style="width: 110px; flex-shrink: 0;">
                    <input
                      v-if="rule.pricing_mode === 'DISCOUNT'"
                      v-model="rule.discount_rate_display"
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="9.9"
                      class="form-control"
                      placeholder="折扣率(如8.5)"
                      style="height: 34px; font-size: 0.82rem; padding: 4px 8px; border-radius: 6px;"
                    />
                    <input
                      v-else
                      v-model="rule.fixed_price"
                      type="number"
                      min="1"
                      class="form-control"
                      placeholder="一口价(蛋能量)"
                      style="height: 34px; font-size: 0.82rem; padding: 4px 8px; border-radius: 6px;"
                    />
                  </div>

                  <!-- 5. 移除规则按钮 (图2 贴纸删除按钮样式) -->
                  <button
                    type="button"
                    class="rule-delete-btn"
                    title="移除此条规则"
                    @click="removeRuleRow(idx)"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>

            <!-- 弹窗底部操作按钮 -->
            <div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--card-border); display: flex; justify-content: flex-end; gap: 12px;">
              <button type="button" class="btn-outline-purple" style="padding: 6px 18px; border-radius: 8px; font-weight: 700;" @click="handleClose">取消</button>
              <button type="submit" class="btn btn-primary-purple" style="padding: 6px 20px; border-radius: 8px; font-weight: 700;">保存活动</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 可视化系列选择器抽屉 -->
  <PromotionTargetPicker
    v-model:open="isPickerOpen"
    :initial-type="pickerType"
    :current-selected-id="selectedPickerSeriesId"
    :sticker-series="availableStickerSeries"
    :canvas-series="availableCanvasSeries"
    @select="handlePickerSelect"
  />
</template>

<style scoped>
.rule-item-box:hover {
  border-color: rgba(139, 92, 246, 0.4) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.rule-delete-btn {
  width: 20px;
  height: 20px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  font-size: 0.72rem;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 1.5px solid #000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  line-height: 1;
  flex-shrink: 0;
  margin-left: auto;
  padding: 0;
  transition: transform 0.15s ease, background 0.15s ease;
}

.rule-delete-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}
</style>
