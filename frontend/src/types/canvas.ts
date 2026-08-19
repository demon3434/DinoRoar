export interface CanvasInstance {
  id?: number
  canvas_set_id?: number
  ratio_name: string // "1:1", "3:4", "9:16"
  background_image_url: string
  width?: number
  height?: number
  safe_zone_top?: number
  safe_zone_bottom?: number
  safe_zone_left?: number
  safe_zone_right?: number
}

export interface CanvasSet {
  id: number
  name: string
  description?: string
  preview_image_url: string
  sort_order: number
  is_active: boolean
  instances: CanvasInstance[]
  created_at?: string
  updated_at?: string
  price?: number
  current_price?: number
  shop_item_id?: number
}
