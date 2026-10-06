import { initData } from './telegram'
import type {
  Order,
  Product,
  TelegramUser,
  CartLine,
} from '../types'

const baseUrl = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('X-Telegram-Init-Data', initData())
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${baseUrl}${path}`, { ...options, headers })
  const payload = (await response.json().catch(() => null)) as
    | { detail?: string | Array<{ msg?: string; loc?: unknown[] }> }
    | null
  if (!response.ok) {
    const detail = payload?.detail
    if (typeof detail === 'string') {
      throw new Error(detail)
    }
    if (Array.isArray(detail) && detail.length) {
      const first = detail[0]
      const msg = first?.msg || 'Maʼlumotlar notoʻgʻri.'
      throw new Error(msg)
    }
    throw new Error('Server bilan aloqa xatosi.')
  }
  return payload as T
}

export function getMe() {
  return request<TelegramUser>('/api/me')
}

export function getProducts(params: { category?: string; search?: string } = {}) {
  const query = new URLSearchParams()
  if (params.category) query.set('category', params.category)
  if (params.search) query.set('search', params.search)
  const suffix = query.toString() ? `?${query}` : ''
  return request<Product[]>(`/api/products${suffix}`)
}

export function getOrders() {
  return request<Order[]>('/api/orders')
}

export function createOrder(payload: {
  phone_number: string
  comment: string
  items: Array<{
    product_id: number
    quantity: number
    size?: string
    color?: string
  }>
}) {
  return request<{ order: Order }>('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getAdminProducts() {
  return request<Product[]>('/api/admin/products')
}

export function addAdminProduct(payload: {
  name: string
  description: string
  category: string
  price: number
  quantity: number
  image_url?: string
  image_urls: string[]
  sizes: string[]
  colors: string[]
}) {
  return request<Product>('/api/admin/products', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function uploadAdminImage(file: File) {
  const body = new FormData()
  body.append('file', file)
  return request<{ url: string }>('/api/admin/images', {
    method: 'POST',
    body,
  })
}

export function updateAdminProduct(id: number, payload: Partial<Product>) {
  return request<Product>(`/api/admin/products/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function addStock(id: number, quantity: number, comment: string) {
  return request<Product>(`/api/admin/products/${id}/stock`, {
    method: 'POST',
    body: JSON.stringify({ quantity, comment }),
  })
}

export function getAdminOrders() {
  return request<Order[]>('/api/admin/orders')
}

export function approveOrder(id: number) {
  return request(`/api/admin/orders/${id}/approve`, { method: 'POST' })
}

export function rejectOrder(id: number) {
  return request(`/api/admin/orders/${id}/reject`, { method: 'POST' })
}

export function cartPayload(lines: CartLine[]) {
  return lines.map((line) => {
    const item: {
      product_id: number
      quantity: number
      size?: string
      color?: string
    } = {
      product_id: line.product.id,
      quantity: line.quantity,
    }
    if (line.size) item.size = line.size
    if (line.color) item.color = line.color
    return item
  })
}
