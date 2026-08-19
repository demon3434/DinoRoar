export interface UserInfo {
  id: number
  username: string
  nickname?: string
  theme?: string
  egg_energy?: number
  is_admin?: boolean
  role?: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user?: UserInfo
}
