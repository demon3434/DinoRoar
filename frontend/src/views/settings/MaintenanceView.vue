<script setup lang="ts">
import { ref } from 'vue'
import apiClient from '@/api/client'
import ConfirmModal from '@/components/common/ConfirmModal.vue'

const loading = ref(false)
const isConfirmModalOpen = ref(false)
const cleanupResult = ref<{ success: boolean; totalDeleted?: number; sizeMB?: string; error?: string } | null>(null)

async function runSystemCleanup() {
  if (loading.value) return
  loading.value = true
  cleanupResult.value = null

  const endpoints = ['/api/admin/cleanup_stickers', '/api/admin/cleanup_canvases', '/api/admin/cleanup']
  let totalDeleted = 0
  let totalFreed = 0

  try {
    for (const ep of endpoints) {
      try {
        const data: any = await apiClient.post(ep)
        totalDeleted += data.deleted_files ? data.deleted_files.length : 0
        totalFreed += data.freed_bytes || 0
      } catch (e) {
        // Continue
      }
    }
    const sizeMB = (totalFreed / 1024 / 1024).toFixed(2)
    cleanupResult.value = {
      success: true,
      totalDeleted,
      sizeMB
    }
  } catch (e) {
    cleanupResult.value = {
      success: false,
      error: '清理过程发生异常，请检查服务器日志。'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="maintenance-view" style="width: 100%;">
    <header style="margin-bottom: 30px; width: 100%;">
      <h2 style="font-size: 1.4rem; font-weight: 800;">🧹 系统清理与物理维护</h2>
      <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">深度维护底层物理存储，防止未关联的废弃附件占用多余空间</p>
    </header>

    <div class="card" style="max-width: 650px; border: 1px solid var(--card-border);">
      <div class="card-title">磁盘维护与冗余清理</div>
      <p style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 25px; line-height: 1.6;">
        “孤儿文件清理”模块将会主动扫描并彻底删除本地硬盘 <code>uploads/attachments/</code> 与贴纸画布中没有被任何日志关联的图片和音视频物理文件，以节省家庭服务器存储空间。
      </p>

      <button
        type="button"
        class="btn btn-primary-purple"
        :disabled="loading"
        @click="isConfirmModalOpen = true"
        style="display: inline-flex; align-items: center; gap: 8px;"
      >
        <span>🧹</span>
        <span>{{ loading ? '正在深度扫描与清理...' : '执行系统清理' }}</span>
      </button>

      <div
        v-if="cleanupResult"
        style="margin-top: 25px; font-size: 0.9rem; padding: 15px; border-radius: 12px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--card-border); line-height: 1.6;"
        :style="{ color: cleanupResult.success ? 'var(--dino-green)' : 'var(--dino-red)' }"
      >
        <template v-if="cleanupResult.success">
          <strong style="font-size: 0.95rem;">✅ 清理完成！</strong><br />
          - 共删除无用文件: <code style="color:var(--text-main); font-weight:bold;">{{ cleanupResult.totalDeleted }}</code> 个<br />
          - 释放物理硬盘空间: <code style="color:var(--text-main); font-weight:bold;">{{ cleanupResult.sizeMB }} MB</code>
        </template>
        <template v-else>
          ❌ {{ cleanupResult.error }}
        </template>
      </div>
    </div>

    <!-- 系统清理二次确认弹层 -->
    <ConfirmModal
      v-model="isConfirmModalOpen"
      title="系统清理确认"
      message="确定要执行系统清理吗？此操作将扫描并彻底删除本地硬盘上未关联的废弃附件物理文件，以释放存储空间。"
      confirm-text="确认清理"
      type="warning"
      @confirm="runSystemCleanup"
    />
  </div>
</template>

<style scoped>
.maintenance-view {
  display: flex;
  flex-direction: column;
}
</style>
