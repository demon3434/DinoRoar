export interface PromotionTarget {
  id?: number
  promotion_id?: number
  target_type: 'ALL' | 'CATEGORY' | 'SERIES' | 'SINGLE' | string
  target_id?: number | null
  target_name?: string
  discount_rate?: number
  special_price?: number
}

export interface PromotionItem {
  id: number
  name: string
  description?: string
  banner_url?: string
  start_time: string
  end_time: string
  is_active: boolean
  sort_order: number
  targets?: PromotionTarget[]
  rules?: any[]
  created_at?: string
  status?: 'ACTIVE' | 'UPCOMING' | 'EXPIRED' | 'DISABLED'
}
