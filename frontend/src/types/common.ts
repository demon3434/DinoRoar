export interface ApiResponse<T = any> {
  success?: boolean
  message?: string
  data?: T
  [key: string]: any
}

export interface PaginationParams {
  page?: number
  pageSize?: number
  keyword?: string
}
