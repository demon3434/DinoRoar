import apiClient from './client'
import type { StickerItem } from '@/types/sticker'

export async function fetchStickersData(): Promise<{ stickers: StickerItem[]; categories: string[]; seriesList: any[] }> {
  const seriesRes: any = await apiClient.get('/api/stickers/config?for_admin=true')
  const seriesList = seriesRes || []
  const categories: string[] = []
  const stickers: StickerItem[] = []

  for (const s of seriesList) {
    if (!categories.includes(s.name)) {
      categories.push(s.name)
    }
    for (const stk of (s.stickers || [])) {
      stickers.push({
        id: stk.id,
        name: stk.name,
        category: s.name,
        image_url: stk.image_url,
        sort_order: stk.sort_order,
        is_active: stk.is_active,
        price: stk.exchange_price || stk.price || 20,
        current_price: stk.current_price,
        shop_item_id: stk.shop_item_id
      })
    }
  }

  return { stickers, categories, seriesList }
}

export async function uploadSticker(formData: FormData): Promise<any> {
  return apiClient.post('/api/stickers/admin/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function updateSticker(id: number, formData: FormData): Promise<any> {
  return apiClient.put(`/api/stickers/admin/${id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function deleteSticker(id: number): Promise<void> {
  return apiClient.delete(`/api/stickers/admin/${id}`)
}

export async function toggleStickerActive(id: number): Promise<any> {
  return apiClient.patch(`/api/stickers/admin/${id}/toggle-active`)
}

export async function exportStickersZip(seriesIds?: number[]): Promise<Blob> {
  const url = seriesIds && seriesIds.length > 0
    ? `/api/stickers/admin/export?series_ids=${seriesIds.join(',')}`
    : '/api/stickers/admin/export'
  return apiClient.get(url, { responseType: 'blob' })
}

export async function previewImportStickersZip(file: File): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.post('/api/stickers/admin/import/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function confirmImportStickersZip(tempToken: string, selectedSeriesNames: string[], conflictResolution: string): Promise<any> {
  return apiClient.post('/api/stickers/admin/import/confirm', {
    temp_token: tempToken,
    selected_series_names: selectedSeriesNames,
    conflict_resolution: conflictResolution
  })
}
