<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { showToast } from '@/utils/toast'

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

const props = defineProps<{
  modelValue: boolean
  tx: TransactionItem | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void
}>()

let mouseDownOnBackdrop = false

function handleBackdropMouseDown(e: MouseEvent) {
  mouseDownOnBackdrop = e.target === e.currentTarget
}

function handleBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget && mouseDownOnBackdrop) {
    emit('update:modelValue', false)
  }
  mouseDownOnBackdrop = false
}

function handleClose() {
  emit('update:modelValue', false)
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.modelValue) {
    handleClose()
  }
}

function copyUUID(uuid: string | null) {
  if (!uuid) return
  navigator.clipboard.writeText(uuid)
  showToast('流水单号已复制到剪贴板！', 'success')
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div
    v-if="modelValue && tx"
    class="drawer-overlay"
    @mousedown="handleBackdropMouseDown"
    @click="handleBackdropClick"
  >
    <div class="receipt-drawer" @click.stop>
      <div class="drawer-header">
        <h3>🧾 蛋能量电子凭证回单</h3>
        <button class="btn-close" type="button" @click="handleClose">✕</button>
      </div>

      <div class="receipt-body">
        <div class="receipt-card">
          <div class="watermark">DINOROAR VERIFIED</div>

          <div class="receipt-top">
            <div class="receipt-status">交易成功 · 权威已记账</div>
            <div
              class="receipt-amount"
              :class="tx.change_amount > 0 ? 'text-emerald' : 'text-amber'"
            >
              {{ tx.change_amount > 0 ? '+' : '' }}{{ tx.change_amount }}
              <span class="unit">蛋能量 🥚</span>
            </div>
          </div>

          <div class="receipt-divider"></div>

          <div class="receipt-rows">
            <div class="receipt-row">
              <span class="label">交易流水号：</span>
              <div class="val-copy">
                <span class="mono-id">{{ tx.request_uuid || `TX_${tx.id}` }}</span>
                <button type="button" class="btn-mini-copy" @click="copyUUID(tx.request_uuid || `TX_${tx.id}`)">
                  复制
                </button>
              </div>
            </div>

            <div class="receipt-row">
              <span class="label">交易时间：</span>
              <span class="val mono-id">{{ tx.created_at }}</span>
            </div>

            <div class="receipt-row">
              <span class="label">孩子账户：</span>
              <span class="val">{{ tx.nickname || tx.username }} (@{{ tx.username }})</span>
            </div>

            <div class="receipt-row">
              <span class="label">业务类型：</span>
              <span class="val highlight">{{ tx.asset_display.title || tx.event_name }}</span>
            </div>

            <div class="receipt-row" v-if="tx.asset_display.subtitle">
              <span class="label">业务明细：</span>
              <span class="val">{{ tx.asset_display.subtitle }}</span>
            </div>

            <div class="receipt-row">
              <span class="label">变动前余额：</span>
              <span class="val mono-id">{{ tx.balance_after - tx.change_amount }} 🥚</span>
            </div>

            <div class="receipt-row">
              <span class="label">变动后结余：</span>
              <span class="val mono-id font-bold text-emerald">{{ tx.balance_after }} 🥚</span>
            </div>
          </div>

          <!-- 实体缩略图与详情 -->
          <div class="receipt-asset-preview" v-if="tx.asset_display.image_url">
            <img
              :src="tx.asset_display.image_url"
              class="receipt-thumb"
              @error="(e) => ((e.target as HTMLElement).style.display = 'none')"
            />
            <div class="asset-meta-box">
              <div class="asset-name">{{ tx.asset_display.title }}</div>
              <div class="asset-extra" v-if="tx.asset_display.detail_info">
                <span v-if="tx.asset_display.detail_info.series_name">
                  系列：{{ tx.asset_display.detail_info.series_name }}
                </span>
                <span v-if="tx.asset_display.detail_info.streak_days">
                  连签：{{ tx.asset_display.detail_info.streak_days }} 天
                </span>
                <span v-if="tx.asset_display.detail_info.incident_date">
                  日期：{{ tx.asset_display.detail_info.incident_date }}
                </span>
              </div>
            </div>
          </div>

          <div class="receipt-footer">
            <p>🦖 恐龙秘密基地能量银行系统电子签章</p>
            <p class="crypto-hash">AUTH-SHA256: {{ tx.id }}9f8a7c2b5d4e1</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
}

.receipt-drawer {
  width: 440px;
  max-width: 90vw;
  background: var(--card-bg, #0f172a);
  height: 100%;
  border-left: 1px solid var(--card-border, rgba(255, 255, 255, 0.1));
  display: flex;
  flex-direction: column;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.5);
  animation: slideIn 0.25s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--card-border, rgba(255, 255, 255, 0.08));
}

.drawer-header h3 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--text-main, #fff);
}

.btn-close {
  background: none;
  border: none;
  color: var(--text-muted, #94a3b8);
  font-size: 18px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.btn-close:hover {
  color: var(--text-main, #fff);
  background: rgba(255, 255, 255, 0.1);
}

.receipt-body {
  padding: 24px 20px;
  overflow-y: auto;
  flex: 1;
}

.receipt-card {
  background: var(--card-bg, rgba(255, 255, 255, 0.9));
  border: 1px dashed var(--card-border, rgba(0, 0, 0, 0.15));
  border-radius: 14px;
  padding: 22px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.watermark {
  position: absolute;
  top: 40%;
  left: 10%;
  font-size: 28px;
  font-weight: 900;
  color: var(--text-muted, rgba(0, 0, 0, 0.04));
  opacity: 0.15;
  transform: rotate(-30deg);
  pointer-events: none;
}

.receipt-status {
  font-size: 0.8rem;
  color: #10b981;
  font-weight: 700;
  text-align: center;
}

.receipt-amount {
  font-size: 2rem;
  font-weight: 800;
  text-align: center;
  margin: 10px 0;
}

.receipt-amount .unit {
  font-size: 1rem;
  font-weight: 600;
}

.receipt-divider {
  border-top: 1px dashed var(--card-border, rgba(0, 0, 0, 0.12));
  margin: 16px 0;
}

.receipt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
  margin-bottom: 12px;
}

.receipt-row .label {
  color: var(--text-muted, #64748b);
}

.receipt-row .val {
  color: var(--text-main, #1e293b);
  font-weight: 600;
}

.val-copy {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mono-id {
  font-family: monospace;
  font-size: 0.78rem;
}

.btn-mini-copy {
  background: var(--input-bg, rgba(0, 0, 0, 0.05));
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.12));
  color: var(--text-main);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-mini-copy:hover {
  background: var(--card-border, rgba(0, 0, 0, 0.1));
}

.receipt-asset-preview {
  margin-top: 16px;
  background: var(--input-bg, rgba(0, 0, 0, 0.03));
  border-radius: 10px;
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

.receipt-thumb {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: contain;
  background: rgba(0, 0, 0, 0.05);
}

.asset-meta-box {
  flex: 1;
}

.asset-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--text-main);
}

.asset-extra {
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.receipt-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 0.7rem;
  color: var(--text-muted, #64748b);
  border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
  padding-top: 14px;
}

.crypto-hash {
  margin-top: 4px;
  font-family: monospace;
}

.text-emerald {
  color: #10b981;
}

.text-amber {
  color: #f59e0b;
}
</style>
