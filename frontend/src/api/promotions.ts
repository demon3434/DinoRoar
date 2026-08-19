import apiClient from './client'
import type { PromotionItem } from '@/types/promotion'

export async function fetchPromotions(params?: any): Promise<any> {
  const res: any = await apiClient.get('/api/admin/promotions', { params })
  return res.items || res || []
}

export async function createPromotion(data: Partial<PromotionItem>): Promise<PromotionItem> {
  return apiClient.post('/api/admin/promotions', data)
}

export async function updatePromotion(id: number, data: Partial<PromotionItem>): Promise<PromotionItem> {
  return apiClient.put(`/api/admin/promotions/${id}`, data)
}

export async function deletePromotion(id: number): Promise<void> {
  return apiClient.delete(`/api/admin/promotions/${id}`)
}

export async function togglePromotionStatus(id: number, isActive: boolean): Promise<PromotionItem> {
  return apiClient.patch(`/api/admin/promotions/${id}/toggle-active`, { is_active: isActive })
}
