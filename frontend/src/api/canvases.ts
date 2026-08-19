import apiClient from './client'
import type { CanvasSet } from '@/types/canvas'

export async function fetchCanvasSetsData(): Promise<{ canvases: CanvasSet[]; seriesList: any[] }> {
  const seriesRes: any = await apiClient.get('/api/canvases/config?for_admin=true')
  const seriesList = seriesRes || []
  const canvases: CanvasSet[] = []

  for (const s of seriesList) {
    for (const cset of (s.sets || [])) {
      canvases.push({
        id: cset.id,
        name: cset.name,
        description: cset.description,
        preview_image_url: cset.preview_image_url || (cset.instances?.[0]?.background_image_url || ''),
        sort_order: cset.sort_order,
        is_active: cset.is_active,
        instances: cset.instances || [],
        price: cset.exchange_price || 50,
        current_price: cset.current_price,
        shop_item_id: cset.shop_item_id
      })
    }
  }

  return { canvases, seriesList }
}

export async function createCanvasSetWithInstances(formData: FormData): Promise<any> {
  return apiClient.post('/api/canvases/admin/set/with-instances', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function updateCanvasSet(id: number, payload: any): Promise<any> {
  return apiClient.put(`/api/canvases/admin/set/${id}`, payload)
}

export async function deleteCanvasSet(id: number): Promise<void> {
  return apiClient.delete(`/api/canvases/admin/set/${id}`)
}

export async function toggleCanvasActive(id: number): Promise<any> {
  return apiClient.patch(`/api/canvases/admin/set/${id}/toggle-active`)
}

export async function exportCanvasZip(seriesIds?: number[]): Promise<Blob> {
  const url = seriesIds && seriesIds.length > 0
    ? `/api/canvases/admin/export?series_ids=${seriesIds.join(',')}`
    : '/api/canvases/admin/export'
  return apiClient.get(url, { responseType: 'blob' })
}

export async function previewImportCanvasZip(file: File): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  return apiClient.post('/api/canvases/admin/import/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function confirmImportCanvasZip(tempToken: string, selectedSeriesNames: string[], conflictResolution: string): Promise<any> {
  return apiClient.post('/api/canvases/admin/import/confirm', {
    temp_token: tempToken,
    selected_series_names: selectedSeriesNames,
    conflict_resolution: conflictResolution
  })
}
