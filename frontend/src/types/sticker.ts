export interface StickerItem {
  id: number
  name: string
  category: string
  image_url: string
  sort_order: number
  is_active: boolean
  created_at?: string
  updated_at?: string
  // Shop item info
  price?: number
  current_price?: number
  shop_item_id?: number
}

export interface StickerCategory {
  name: string
  count: number
}
