export type Category = 'hudi' | 'futbolka' | 'suvenir' | string

export interface Product {
  id: number
  name: string
  description: string
  price: number
  quantity: number
  image_url: string | null
  image_urls: string[]
  category: Category
  sizes: string[]
  colors: string[]
  is_active: boolean
  created_at: string
}

export interface CartLine {
  product: Product
  quantity: number
  size?: string
  color?: string
}

export interface TelegramUser {
  id: number
  first_name: string
  last_name: string
  username: string | null
  is_admin: boolean
}

export interface Order {
  id: number
  user_id: number
  user_name: string | null
  phone_number: string
  comment: string
  total_price: number
  status: 'pending' | 'approved' | 'rejected'
  created_at: string
  items?: OrderItem[]
}

export interface OrderItem {
  id: number
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  size?: string | null
  color?: string | null
}
