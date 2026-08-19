<script setup lang="ts">
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'
import { showToast } from '@/utils/toast'

interface StreakRuleItem {
  days: number
  reward: number
}

const loading = ref(false)
const saving = ref(false)
const simulating = ref(false)
const simulationResult = ref<any>(null)

const config = ref({
  base_min: 1,
  base_max: 3,
  crit_rate: 0.2,
  crit_min: 35,
  crit_max: 77,
  streak_enabled: true
})

const streakList = ref<StreakRuleItem[]>([
  { days: 3, reward: 10 },
  { days: 7, reward: 30 }
])

function parseStreakJson(jsonStr: string) {
  try {
    const obj = JSON.parse(jsonStr || '{}')
    const list: StreakRuleItem[] = Object.entries(obj).map(([k, v]) => ({
      days: Number(k),
      reward: Number(v)
    }))
    list.sort((a, b) => a.days - b.days)
    streakList.value = list.length > 0 ? list : [{ days: 3, reward: 10 }, { days: 7, reward: 30 }]
  } catch {
    streakList.value = [{ days: 3, reward: 10 }, { days: 7, reward: 30 }]
  }
}

function serializeStreakList(): string {
  const obj: Record<string, number> = {}
  streakList.value.forEach((item) => {
    if (item.days > 0 && item.reward > 0) {
      obj[String(item.days)] = Number(item.reward)
    }
  })
  return JSON.stringify(obj)
}

function addStreakRule(days = 1, reward = 5) {
  const existingDays = new Set(streakList.value.map((s) => s.days))
  let targetDays = days
  while (existingDays.has(targetDays)) {
    targetDays++
  }
  streakList.value.push({ days: targetDays, reward })
  streakList.value.sort((a, b) => a.days - b.days)
}

function removeStreakRule(index: number) {
  streakList.value.splice(index, 1)
}

function addPresetStreak(days: number, reward: number) {
  const idx = streakList.value.findIndex((s) => s.days === days)
  if (idx !== -1) {
    showToast(`连签第 ${days} 天的阶梯规则已存在！`, 'info')
    return
  }
  streakList.value.push({ days, reward })
  streakList.value.sort((a, b) => a.days - b.days)
}

async function fetchConfig() {
  loading.value = true
  try {
    const data: any = await apiClient.get('/api/admin/checkin/config')
    config.value = {
      base_min: data.base_min,
      base_max: data.base_max,
      crit_rate: data.crit_rate,
      crit_min: data.crit_min,
      crit_max: data.crit_max,
      streak_enabled: data.streak_enabled
    }
    parseStreakJson(data.streak_rules_json)
  } catch (e: any) {
    showToast(e.response?.data?.detail || '获取签到配置失败', 'error')
  } finally {
    loading.value = false
  }
}

function runSimulation() {
  const baseMin = Number(config.value.base_min) || 0
  const baseMax = Number(config.value.base_max) || 0
  const critRate = Number(config.value.crit_rate) || 0
  const critMin = Number(config.value.crit_min) || 0
  const critMax = Number(config.value.crit_max) || 0
  const streakEnabled = config.value.streak_enabled

  if (baseMin > baseMax) {
    showToast('日常保底能量不能大于最高能量！', 'error')
    return
  }
  if (critMin > critMax) {
    showToast('暴击最小能量不能大于最高能量！', 'error')
    return
  }

  simulating.value = true
  const streakMap: Record<string, number> = {}
  streakList.value.forEach((s) => {
    if (s.days > 0 && s.reward > 0) {
      streakMap[String(s.days)] = s.reward
    }
  })

  let total = 0
  let critCount = 0
  const SAMPLES = 1000

  for (let i = 0; i < SAMPLES; i++) {
    const isCrit = Math.random() < critRate
    let reward = 0
    if (isCrit) {
      critCount++
      reward = Math.floor(Math.random() * (critMax - critMin + 1)) + critMin
    } else {
      reward = Math.floor(Math.random() * (baseMax - baseMin + 1)) + baseMin
    }
    total += reward
  }

  const avgReward = (total / SAMPLES).toFixed(1)
  const critPercent = ((critCount / SAMPLES) * 100).toFixed(1)

  let weekBonus = 0
  if (streakEnabled) {
    for (let day = 1; day <= 7; day++) {
      weekBonus += Number(streakMap[String(day)] || 0)
    }
  }
  const weeklyTotalEstimate = Math.round(Number(avgReward) * 7 + weekBonus)

  simulationResult.value = {
    avgReward,
    critPercent,
    critCount,
    weeklyTotalEstimate,
    stickerEquiv: (weeklyTotalEstimate / 20).toFixed(1),
    canvasEquiv: (weeklyTotalEstimate / 50).toFixed(1)
  }
  simulating.value = false
  showToast('🎲 1000 次蒙特卡洛抽样测算完成！', 'success')
}

async function handleSave() {
  const baseMin = Number(config.value.base_min)
  const baseMax = Number(config.value.base_max)
  const critRate = Number(config.value.crit_rate)
  const critMin = Number(config.value.crit_min)
  const critMax = Number(config.value.crit_max)

  if (baseMin > baseMax) {
    showToast('日常保底能量不能大于最高能量！', 'error')
    return
  }
  if (critMin > critMax) {
    showToast('暴击最小能量不能大于最高能量！', 'error')
    return
  }
  if (critRate < 0 || critRate > 1) {
    showToast('暴击触发率必须在 0 到 1 之间（例如 0.15 代表 15%）！', 'error')
    return
  }

  const streakJson = serializeStreakList()

  saving.value = true
  try {
    await apiClient.post('/api/admin/checkin/config', {
      base_min: baseMin,
      base_max: baseMax,
      crit_rate: critRate,
      crit_min: critMin,
      crit_max: critMax,
      streak_enabled: config.value.streak_enabled,
      streak_rules_json: streakJson
    })
    showToast('🎉 签到参数配置保存成功并已即时生效！', 'success')
    fetchConfig()
  } catch (e: any) {
    showToast(e.response?.data?.detail || '保存配置失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="checkin-container">
    <!-- 顶部 Header (与全站标准对齐) -->
    <header class="page-header">
      <div>
        <h2 class="page-title">
          <span>🥚</span> 每日签到与蛋能量调控中心
        </h2>
      </div>
      <button class="btn btn-outline-purple" @click="fetchConfig" :disabled="loading">
        <span :class="{ spinning: loading }">🔄</span> 刷新参数
      </button>
    </header>

    <!-- 2×2 网格布局 (左右等高严格对称) -->
    <div class="checkin-grid">
      <!-- 【第 1 行左侧】⚙️ 算法核心参数设置 -->
      <div class="card config-card">
        <div class="card-header">
          <div class="card-title-group">
            <span class="card-icon">⚙️</span>
            <h3 class="card-title">算法核心参数设置</h3>
          </div>
          <span class="card-tag">实时热更新 · 权威控制</span>
        </div>

        <form @submit.prevent="handleSave" class="config-form">
          <!-- 1. 基础日常奖励区间 -->
          <div class="param-section section-base">
            <div class="section-title text-base">
              <span>🎁</span> 基础日常奖励区间 (日常均匀随机)
            </div>
            <div class="form-row-2">
              <div class="form-group">
                <label class="form-label">日常保底蛋能量 (base_min)</label>
                <input
                  v-model.number="config.base_min"
                  type="number"
                  class="form-control"
                  required
                  min="1"
                  max="1000"
                />
              </div>
              <div class="form-group">
                <label class="form-label">日常最高蛋能量 (base_max)</label>
                <input
                  v-model.number="config.base_max"
                  type="number"
                  class="form-control"
                  required
                  min="1"
                  max="1000"
                />
              </div>
            </div>
          </div>

          <!-- 2. 欧皇暴击机制 -->
          <div class="param-section section-crit">
            <div class="section-title text-crit">
              <span>🔥</span> 欧皇大暴击机制 (Critical Hit 随机惊喜)
            </div>
            <div class="form-row-3">
              <div class="form-group">
                <label class="form-label">暴击概率 (0~1，如0.2=20%)</label>
                <input
                  v-model.number="config.crit_rate"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  class="form-control"
                  required
                />
              </div>
              <div class="form-group">
                <label class="form-label">暴击最小能量 (crit_min)</label>
                <input
                  v-model.number="config.crit_min"
                  type="number"
                  class="form-control"
                  required
                  min="1"
                  max="5000"
                />
              </div>
              <div class="form-group">
                <label class="form-label">暴击最高能量 (crit_max)</label>
                <input
                  v-model.number="config.crit_max"
                  type="number"
                  class="form-control"
                  required
                  min="1"
                  max="5000"
                />
              </div>
            </div>
          </div>

          <!-- 3. 连续签到阶梯奖励 (可视化交互，彻底告别手写 JSON) -->
          <div class="param-section section-streak">
            <div class="section-header">
              <div class="section-title text-streak">
                <span>👣</span> 连续签到阶梯奖励 (Streak Bonus)
              </div>
              <label class="checkbox-label">
                <input v-model="config.streak_enabled" type="checkbox" class="custom-checkbox" />
                <span>启用连签阶梯</span>
              </label>
            </div>

            <div v-if="config.streak_enabled" class="streak-body">
              <div class="streak-list">
                <div
                  v-for="(item, index) in streakList"
                  :key="index"
                  class="streak-item-row"
                >
                  <span class="streak-label">连签满</span>
                  <input
                    v-model.number="item.days"
                    type="number"
                    min="1"
                    max="365"
                    class="form-control streak-input-days"
                    placeholder="天数"
                  />
                  <span class="streak-label">天 ➜ 额外送</span>
                  <input
                    v-model.number="item.reward"
                    type="number"
                    min="1"
                    max="5000"
                    class="form-control streak-input-reward"
                    placeholder="蛋能量"
                  />
                  <span class="streak-unit">🥚</span>
                  <button
                    type="button"
                    class="btn-delete-streak"
                    title="删除该阶梯"
                    @click="removeStreakRule(index)"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              <div class="streak-actions-bar">
                <button
                  type="button"
                  class="btn-sm btn-outline-purple btn-add-streak"
                  @click="addStreakRule()"
                >
                  ➕ 添加连签阶梯
                </button>
                <div class="preset-group">
                  <span class="preset-tip">快捷预设:</span>
                  <button type="button" class="btn-preset" @click="addPresetStreak(3, 10)">+ 第3天</button>
                  <button type="button" class="btn-preset" @click="addPresetStreak(7, 30)">+ 第7天</button>
                  <button type="button" class="btn-preset" @click="addPresetStreak(14, 60)">+ 第14天</button>
                  <button type="button" class="btn-preset" @click="addPresetStreak(30, 150)">+ 第30天</button>
                </div>
              </div>
            </div>
          </div>

          <!-- 保存按钮 -->
          <div class="form-footer">
            <button
              type="submit"
              class="btn btn-primary-purple btn-save"
              :disabled="saving"
            >
              <span>💾</span> {{ saving ? '保存中...' : '保存配置并即时生效' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 【第 1 行右侧】📖 规则指南与配置建议 (与左侧配置卡片严格等高) -->
      <div class="card guide-card">
        <div class="card-header">
          <div class="card-title-group">
            <span class="card-icon">📖</span>
            <h3 class="card-title">规则指南与配置建议</h3>
          </div>
          <span class="card-tag">经济模型参照</span>
        </div>

        <div class="guide-content">
          <div class="guide-block">
            <div class="guide-item-title text-base">
              <span>1️⃣</span> 基础日常奖励（平时的零花钱）
            </div>
            <p class="guide-desc">
              孩子每天打卡的底线收益。系统在【保底值】与【最高值】之间均匀随机给出一个数值，确保孩子每天都有稳定的打卡成就感。
            </p>
          </div>

          <div class="guide-block">
            <div class="guide-item-title text-crit">
              <span>2️⃣</span> 欧皇大暴击（抽大奖的小惊喜）
            </div>
            <p class="guide-desc">
              天天拿基础分容易平淡。设置 10%~20%（填 0.1~0.2）的小概率触发暴击，中奖时手机跳出“欧皇暴击! 💥”并奖励大量能量，极具期待感。
            </p>
          </div>

          <div class="guide-block">
            <div class="guide-item-title text-streak">
              <span>3️⃣</span> 连续签到阶梯（培养坚持好习惯）
            </div>
            <p class="guide-desc">
              鼓励孩子天天坚持不间断。比如第 3 天送 10 能量，满 7 天送 30 能量。让孩子在坚持周期节点获得丰厚全勤大奖。
            </p>
          </div>

          <div class="guide-reference-box">
            <div class="ref-title">🛒 商城兑换定价标杆参考：</div>
            <div class="ref-items">
              <span class="ref-item">🎨 恐龙贴纸：<strong>20 蛋能量 / 张</strong></span>
              <span class="ref-item">🖼️ 背景画布：<strong>50 蛋能量 / 套</strong></span>
            </div>
            <div class="ref-summary">
              📌 <strong>推荐平衡配置</strong>：日常 1~3 分，暴击 0.2 (35~77 分)，连签 3天送10、7天送30。孩子每周全勤约攒 120 能量，够换 6 张贴纸，节奏最适中！
            </div>
          </div>
        </div>
      </div>

      <!-- 【第 2 行左侧】🎲 期望收益模拟测算沙盘 (按钮与结果一体化内聚) -->
      <div class="card simulation-card">
        <div class="card-header">
          <div class="card-title-group">
            <span class="card-icon">🎲</span>
            <h3 class="card-title">期望收益模拟测算沙盘</h3>
          </div>
          <button
            type="button"
            class="btn btn-primary-purple btn-sim-trigger"
            :disabled="simulating"
            @click="runSimulation"
          >
            <span :class="{ spinning: simulating }">🎲</span> 立即模拟 1000 次签到
          </button>
        </div>

        <div class="simulation-body">
          <div v-if="!simulationResult" class="sim-placeholder">
            <span class="sim-placeholder-icon">📊</span>
            <p>点击右上角的 <strong>「立即模拟 1000 次签到」</strong> 按钮</p>
            <small>系统将在 0.01 秒内模拟 1000 个孩子的打卡过程，为您测算实际收益与购买力</small>
          </div>

          <div v-else class="sim-result-panel">
            <div class="sim-kpi-grid">
              <div class="sim-kpi-box">
                <div class="kpi-label">单次平均期望收益</div>
                <div class="kpi-value text-base">🥚 {{ simulationResult.avgReward }}</div>
                <div class="kpi-sub">平均每次敲蛋所获</div>
              </div>
              <div class="sim-kpi-box">
                <div class="kpi-label">模拟暴击触发率</div>
                <div class="kpi-value text-crit">💥 {{ simulationResult.critPercent }}%</div>
                <div class="kpi-sub">1000次中暴击 {{ simulationResult.critCount }} 次</div>
              </div>
              <div class="sim-kpi-box">
                <div class="kpi-label">每周全勤预估总获</div>
                <div class="kpi-value text-streak">🎁 约 {{ simulationResult.weeklyTotalEstimate }} 🥚</div>
                <div class="kpi-sub">连签 7 天含阶梯加成</div>
              </div>
            </div>

            <div class="sim-purchasing-box">
              <div class="purchasing-title">🏷️ 商城购买力等效折算：</div>
              <div class="purchasing-desc">
                按当前参数测算，孩子每周全勤打卡攒下的蛋能量，大约可兑换
                <strong>{{ simulationResult.stickerEquiv }} 张贴纸</strong> 或
                <strong>{{ simulationResult.canvasEquiv }} 套画布</strong>。
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 【第 2 行右侧】💡 测算功能介绍与使用指南 (与左侧沙盘严格等高) -->
      <div class="card simulation-guide-card">
        <div class="card-header">
          <div class="card-title-group">
            <span class="card-icon">💡</span>
            <h3 class="card-title">测算功能介绍与使用方法</h3>
          </div>
          <span class="card-tag">调参辅助工具</span>
        </div>

        <div class="guide-content">
          <div class="guide-block">
            <div class="guide-item-title text-base">
              <span>❓</span> 为什么要提供模拟测算？
            </div>
            <p class="guide-desc">
              签到算法融合了“随机波动”、“暴击概率”和“连续签到阶梯奖励”。仅靠心算难以准确预估出孩子一个星期到底能攒下多少能量。模拟沙盘利用大数据抽样快速得出精准期望。
            </p>
          </div>

          <div class="guide-block">
            <div class="guide-item-title text-crit">
              <span>🎯</span> 如何根据测算结果调整参数？
            </div>
            <p class="guide-desc">
              重点观察<strong>【每周全勤预估总获】</strong>：
              <br />• 若每周全勤 <strong>> 200 能量</strong>：能量产出过快，商城贴纸很容易被快速兑换完；
              <br />• 若每周全勤 <strong>&lt; 50 能量</strong>：能量偏少，孩子需要两周才能攒一张贴纸，容易失去积极性；
              <br />• <strong>黄金节奏</strong>：每周全勤 <strong>100 ~ 130 能量</strong>，大约可换 5~6 张贴纸。
            </p>
          </div>

          <div class="workflow-box">
            <div class="workflow-title">🔄 推荐的 3 步调优流程：</div>
            <div class="workflow-steps">
              <span class="step-chip">① 在左上方调整数值</span>
              <span class="step-arrow">➔</span>
              <span class="step-chip">② 点左下方立即模拟</span>
              <span class="step-arrow">➔</span>
              <span class="step-chip">③ 满意后点保存生效</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.checkin-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  gap: 16px;
}

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

/* 2×2 网格布局 */
.checkin-grid {
  display: grid;
  grid-template-columns: 1.18fr 1fr;
  gap: 20px;
  align-items: stretch;
}

@media (max-width: 1120px) {
  .checkin-grid {
    grid-template-columns: 1fr;
  }
}

/* 卡片通用 */
.card {
  background: var(--card-bg, rgba(255, 255, 255, 0.85));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  font-size: 1.2rem;
}

.card-title {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: var(--text-main);
}

.card-tag {
  font-size: 0.75rem;
  color: var(--text-muted, #64748b);
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

/* 参数区块 */
.param-section {
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 14px;
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
}

.section-base {
  background: rgba(59, 130, 246, 0.03);
  border-color: rgba(59, 130, 246, 0.15);
}

.section-crit {
  background: rgba(239, 68, 68, 0.03);
  border-color: rgba(239, 68, 68, 0.18);
}

.section-streak {
  background: rgba(16, 185, 129, 0.03);
  border-color: rgba(16, 185, 129, 0.18);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  font-weight: 800;
  font-size: 0.88rem;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.section-header .section-title {
  margin-bottom: 0;
}

.text-base { color: #3b82f6; }
.text-crit { color: #ef4444; }
.text-streak { color: #10b981; }

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-row-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 0.78rem;
  color: var(--text-muted, #64748b);
  font-weight: 600;
}

.form-control {
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--input-border, rgba(0, 0, 0, 0.12));
  color: var(--text-main);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85rem;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.checkbox-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--text-main);
  cursor: pointer;
}

.custom-checkbox {
  accent-color: #10b981;
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* 可视化连签阶梯 */
.streak-body {
  margin-top: 10px;
}

.streak-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}

.streak-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card-bg, rgba(255, 255, 255, 0.6));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  padding: 6px 10px;
  border-radius: 8px;
}

.streak-label {
  font-size: 0.8rem;
  color: var(--text-main);
  white-space: nowrap;
  font-weight: 600;
}

.streak-input-days {
  width: 65px;
  height: 30px;
  text-align: center;
  font-weight: 700;
}

.streak-input-reward {
  width: 80px;
  height: 30px;
  text-align: center;
  font-weight: 800;
  color: #10b981;
}

.streak-unit {
  font-size: 0.85rem;
}

.btn-delete-streak {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  font-size: 0.85rem;
  border-radius: 4px;
  margin-left: auto;
  opacity: 0.7;
  transition: opacity 0.15s;
}

.btn-delete-streak:hover {
  opacity: 1;
}

.streak-actions-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.btn-add-streak {
  height: 30px;
  padding: 0 10px;
  font-size: 0.78rem;
  font-weight: 700;
}

.preset-group {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.preset-tip {
  font-size: 0.74rem;
  color: var(--text-muted, #64748b);
}

.btn-preset {
  background: var(--input-bg, rgba(0, 0, 0, 0.04));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.1));
  color: var(--text-main);
  border-radius: 6px;
  font-size: 0.74rem;
  padding: 2px 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-preset:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: #10b981;
  color: #059669;
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
}

.btn-save {
  height: 36px;
  padding: 0 20px;
  font-size: 0.86rem;
  font-weight: 700;
}

/* 指南区 */
.guide-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
  flex: 1;
}

.guide-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.guide-item-title {
  font-size: 0.88rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 6px;
}

.guide-desc {
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-muted, #64748b);
  line-height: 1.55;
}

.guide-reference-box {
  background: var(--input-bg, rgba(0, 0, 0, 0.03));
  border: 1px dashed var(--card-border, rgba(0, 0, 0, 0.15));
  border-radius: 10px;
  padding: 12px 14px;
  margin-top: auto;
}

.ref-title {
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 6px;
}

.ref-items {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: var(--text-muted, #64748b);
  margin-bottom: 8px;
}

.ref-item strong {
  color: var(--text-main);
}

.ref-summary {
  font-size: 0.78rem;
  color: var(--text-main);
  line-height: 1.5;
  border-top: 1px solid var(--card-border, rgba(0, 0, 0, 0.06));
  padding-top: 6px;
}

/* 测算沙盘 */
.btn-sim-trigger {
  height: 32px;
  padding: 0 12px;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.simulation-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.sim-placeholder {
  text-align: center;
  padding: 30px 10px;
  color: var(--text-muted, #64748b);
}

.sim-placeholder-icon {
  font-size: 2.2rem;
  display: block;
  margin-bottom: 8px;
}

.sim-placeholder p {
  margin: 0 0 4px 0;
  font-size: 0.88rem;
  color: var(--text-main);
}

.sim-placeholder small {
  font-size: 0.78rem;
}

.sim-result-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.sim-kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}

.sim-kpi-box {
  background: var(--input-bg, rgba(0, 0, 0, 0.03));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-label {
  font-size: 0.74rem;
  color: var(--text-muted, #64748b);
  font-weight: 600;
}

.kpi-value {
  font-size: 1.25rem;
  font-weight: 800;
  margin: 2px 0;
}

.kpi-sub {
  font-size: 0.7rem;
  color: var(--text-muted, #94a3b8);
}

.sim-purchasing-box {
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.2);
  border-radius: 10px;
  padding: 12px 14px;
}

.purchasing-title {
  font-size: 0.82rem;
  font-weight: 800;
  color: #8b5cf6;
  margin-bottom: 4px;
}

.purchasing-desc {
  font-size: 0.82rem;
  color: var(--text-main);
  line-height: 1.5;
}

.purchasing-desc strong {
  color: #7c3aed;
}

/* 调优流程 */
.workflow-box {
  background: var(--input-bg, rgba(0, 0, 0, 0.03));
  border-radius: 10px;
  padding: 12px 14px;
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.08));
  margin-top: auto;
}

.workflow-title {
  font-size: 0.82rem;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 8px;
}

.workflow-steps {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.step-chip {
  background: var(--card-bg, rgba(255, 255, 255, 0.8));
  border: 1px solid var(--card-border, rgba(0, 0, 0, 0.1));
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.76rem;
  font-weight: 700;
  color: var(--text-main);
}

.step-arrow {
  color: var(--text-muted, #94a3b8);
  font-size: 0.8rem;
}

.spinning {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>
