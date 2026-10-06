<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  ChevronLeft,
  ClipboardList,
  Minus,
  PackagePlus,
  Plus,
  Search,
  ShoppingBag,
  ShoppingCart,
  ShieldCheck,
  Trash2,
  X,
} from 'lucide-vue-next'
import {
  addAdminProduct,
  addStock,
  approveOrder,
  cartPayload,
  createOrder,
  getAdminOrders,
  getAdminProducts,
  getMe,
  getOrders,
  getProducts,
  rejectOrder,
  uploadAdminImage,
} from './lib/api'
import {
  haptic,
  hideBackButton,
  hideMainButton,
  initTelegram,
  setMainButton,
  showBackButton,
} from './lib/telegram'
import type { CartLine, Order, Product, TelegramUser } from './types'

type View = 'shop' | 'orders' | 'admin'

const user = ref<TelegramUser | null>(null)
const products = ref<Product[]>([])
const orders = ref<Order[]>([])
const adminProducts = ref<Product[]>([])
const adminOrders = ref<Order[]>([])
const cart = ref<CartLine[]>([])
const selected = ref<Product | null>(null)
const selectedSize = ref<string | undefined>()
const selectedColor = ref<string | undefined>()
const view = ref<View>('shop')
const category = ref('all')
const search = ref('')
const loading = ref(true)
const error = ref('')
const toast = ref('')
const checkoutOpen = ref(false)
const cartOpen = ref(false)
const phone = ref('')
const comment = ref('')
const submitting = ref(false)
const showAdminForm = ref(false)
const imageFile = ref<File | null>(null)
const stockProduct = ref<Product | null>(null)
const stockQuantity = ref(1)
const stockComment = ref('')

const newProduct = ref({
  name: '',
  description: '',
  category: 'suvenir',
  price: 0,
  quantity: 0,
  image_url: '',
  sizes: '',
  colors: '',
})

const categories = computed(() => [
  { key: 'all', label: 'Barchasi' },
  ...Array.from(new Set(products.value.map((product) => product.category)))
    .filter(Boolean)
    .map((key) => ({ key, label: categoryLabel(key) })),
])

const filteredProducts = computed(() => {
  const needle = search.value.trim().toLocaleLowerCase()
  return products.value.filter((product) => {
    const categoryMatches =
      category.value === 'all' || product.category === category.value
    const searchMatches =
      !needle ||
      product.name.toLocaleLowerCase().includes(needle) ||
      product.description.toLocaleLowerCase().includes(needle)
    return categoryMatches && searchMatches
  })
})

const cartTotal = computed(() =>
  cart.value.reduce((sum, line) => sum + line.product.price * line.quantity, 0),
)

const cartCount = computed(() =>
  cart.value.reduce((sum, line) => sum + line.quantity, 0),
)

function categoryLabel(value: string) {
  return (
    {
      hudi: 'Xudi',
      futbolka: 'Futbolka',
      suvenir: 'Suvenir',
    }[value] || value
  )
}

function money(value: number) {
  return `${new Intl.NumberFormat('uz-UZ').format(value)} so'm`
}

function imageFor(product: Product) {
  return product.image_urls?.[0] || product.image_url || ''
}

function notify(message: string) {
  toast.value = message
  window.setTimeout(() => {
    toast.value = ''
  }, 2800)
}

async function loadCatalog() {
  loading.value = true
  error.value = ''
  try {
    products.value = await getProducts()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Katalog yuklanmadi.'
  } finally {
    loading.value = false
  }
}

function openProduct(product: Product) {
  selected.value = product
  selectedSize.value = product.sizes?.[0]
  selectedColor.value = product.colors?.[0]
  haptic('light')
}

function addProduct(product: Product, size?: string, color?: string) {
  const existing = cart.value.find(
    (line) =>
      line.product.id === product.id &&
      line.size === size &&
      line.color === color,
  )
  if (existing) {
    if (existing.quantity >= product.quantity) {
      notify('Ombordagi mavjud miqdor tugadi.')
      return
    }
    existing.quantity += 1
  } else {
    cart.value.push({ product, quantity: 1, size, color })
  }
  selected.value = null
  haptic('medium')
  notify('Savatga qo‘shildi')
}

function increment(line: CartLine) {
  if (line.quantity >= line.product.quantity) {
    notify('Ombordagi mavjud miqdor tugadi.')
    return
  }
  line.quantity += 1
  haptic('light')
}

function decrement(line: CartLine) {
  if (line.quantity === 1) {
    cart.value = cart.value.filter((item) => item !== line)
  } else {
    line.quantity -= 1
  }
}

function removeLine(line: CartLine) {
  cart.value = cart.value.filter((item) => item !== line)
}

function openCheckout() {
  if (!cart.value.length) {
    notify('Savat bo‘sh.')
    return
  }
  cartOpen.value = false
  checkoutOpen.value = true
}

function openCart() {
  cartOpen.value = true
}

async function submitOrder() {
  const phoneNumber = phone.value.trim()
  const digits = phoneNumber.replace(/\D/g, '')
  if (digits.length < 9) {
    notify('Telefon raqamni to‘liq kiriting (masalan +998901234567).')
    return
  }
  if (!cart.value.length) {
    notify('Savat bo‘sh.')
    return
  }
  submitting.value = true
  try {
    const result = await createOrder({
      phone_number: phoneNumber,
      comment: comment.value.trim(),
      items: cartPayload(cart.value),
    })
    cart.value = []
    checkoutOpen.value = false
    phone.value = ''
    comment.value = ''
    notify(`Buyurtma #${result.order.id} qabul qilindi`)
    await loadCatalog()
    view.value = 'orders'
    await loadOrders()
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Buyurtma yuborilmadi.')
  } finally {
    submitting.value = false
  }
}

async function loadOrders() {
  try {
    orders.value = await getOrders()
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Buyurtmalar yuklanmadi.')
  }
}

async function loadAdmin() {
  if (!user.value?.is_admin) return
  try {
    ;[adminProducts.value, adminOrders.value] = await Promise.all([
      getAdminProducts(),
      getAdminOrders(),
    ])
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Admin ma’lumotlari yuklanmadi.')
  }
}

async function submitProduct() {
  try {
    const uploadedImage = imageFile.value
      ? await uploadAdminImage(imageFile.value)
      : null
    await addAdminProduct({
      ...newProduct.value,
      image_url: uploadedImage?.url || newProduct.value.image_url,
      image_urls: uploadedImage?.url
        ? [uploadedImage.url]
        : newProduct.value.image_url
          ? [newProduct.value.image_url]
          : [],
      sizes: splitValues(newProduct.value.sizes),
      colors: splitValues(newProduct.value.colors),
    })
    notify('Mahsulot qo‘shildi')
    showAdminForm.value = false
    imageFile.value = null
    newProduct.value = {
      name: '',
      description: '',
      category: 'suvenir',
      price: 0,
      quantity: 0,
      image_url: '',
      sizes: '',
      colors: '',
    }
    await loadAdmin()
    await loadCatalog()
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Mahsulot qo‘shilmadi.')
  }
}

function chooseImage(event: Event) {
  const input = event.target as HTMLInputElement
  imageFile.value = input.files?.[0] || null
}

function splitValues(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function openStock(product: Product) {
  stockProduct.value = product
  stockQuantity.value = 1
  stockComment.value = ''
}

async function submitStock() {
  if (!stockProduct.value) return
  try {
    await addStock(
      stockProduct.value.id,
      stockQuantity.value,
      stockComment.value,
    )
    notify('Kirim saqlandi')
    stockProduct.value = null
    await loadAdmin()
    await loadCatalog()
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Kirim saqlanmadi.')
  }
}

async function updateOrder(id: number, action: 'approve' | 'reject') {
  try {
    if (action === 'approve') await approveOrder(id)
    else await rejectOrder(id)
    notify(action === 'approve' ? 'Buyurtma qabul qilindi' : 'Buyurtma rad etildi')
    await loadAdmin()
  } catch (reason) {
    notify(reason instanceof Error ? reason.message : 'Buyurtma yangilanmadi.')
  }
}

function statusLabel(status: Order['status']) {
  return {
    pending: 'Kutilmoqda',
    approved: 'Qabul qilindi',
    rejected: 'Bekor qilindi',
  }[status]
}

function setView(next: View) {
  view.value = next
  if (next === 'orders') void loadOrders()
  if (next === 'admin') void loadAdmin()
}

function syncMainButton() {
  if (view.value === 'shop' && cart.value.length) {
    setMainButton(`Savat · ${money(cartTotal.value)}`, openCart)
  } else {
    hideMainButton()
  }
}

function syncBackButton() {
  const modalOpen = Boolean(selected.value || cartOpen.value || checkoutOpen.value || stockProduct.value)
  if (modalOpen) {
    showBackButton(() => {
      selected.value = null
      cartOpen.value = false
      checkoutOpen.value = false
      stockProduct.value = null
    })
  } else if (view.value !== 'shop') {
    showBackButton(() => setView('shop'))
  } else {
    hideBackButton()
  }
}

watch([cart, view, selected, cartOpen, checkoutOpen, stockProduct], () => {
  syncMainButton()
  syncBackButton()
}, { deep: true })

onMounted(async () => {
  initTelegram()
  try {
    user.value = await getMe()
    await loadCatalog()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Ilova yuklanmadi.'
  }
  syncMainButton()
  syncBackButton()
})
</script>

<template>
  <main class="min-h-screen pb-8">
    <header class="sticky top-0 z-20 border-b border-slate-200/70 bg-[var(--tg-bg)]/90 px-4 pb-3 pt-[max(14px,env(safe-area-inset-top))] backdrop-blur-xl">
      <div class="mx-auto flex max-w-2xl items-center justify-between">
        <div class="flex items-center gap-3">
          <img
            class="h-12 w-12 rounded-full bg-white object-contain p-0.5 shadow-sm"
            src="/tatu-logo.png"
            alt="TATU logotipi"
          />
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.18em] text-brand">TATU</p>
            <h1 class="text-xl font-extrabold tracking-tight">Brend Do‘koni</h1>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button class="icon-button" title="Savat" @click="openCart">
            <ShoppingCart :size="20" />
            <span v-if="cartCount" class="cart-badge">{{ cartCount }}</span>
          </button>
          <button v-if="user?.is_admin" class="icon-button" title="Admin" @click="setView('admin')">
            <ShieldCheck :size="20" />
          </button>
        </div>
      </div>
    </header>

    <section class="mx-auto max-w-2xl px-4 pt-5">
      <div class="mb-5 flex items-end justify-between">
        <div>
          <p class="text-sm text-[var(--tg-hint)]">Assalomu alaykum{{ user?.first_name ? `, ${user.first_name}` : '' }} 👋</p>
          <h2 class="mt-1 text-2xl font-black">O‘zingizga mosini tanlang</h2>
        </div>
        <ShoppingBag class="text-brand" :size="30" />
      </div>

      <div v-if="view === 'shop'">
        <div class="relative mb-4">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--tg-hint)]" :size="18" />
          <input v-model="search" class="input pl-11" placeholder="Mahsulot qidirish..." />
        </div>

        <div class="hide-scrollbar mb-5 flex gap-2 overflow-x-auto pb-1">
          <button
            v-for="item in categories"
            :key="item.key"
            class="chip whitespace-nowrap"
            :class="{ 'chip-active': category === item.key }"
            @click="category = item.key"
          >
            {{ item.label }}
          </button>
        </div>

        <div v-if="loading" class="grid grid-cols-2 gap-3">
          <div v-for="item in 4" :key="item" class="skeleton h-64" />
        </div>
        <div v-else-if="error" class="empty-state">
          <p>{{ error }}</p>
          <button class="primary-button mt-4" @click="loadCatalog">Qayta urinish</button>
        </div>
        <div v-else-if="!filteredProducts.length" class="empty-state">
          <PackagePlus class="mx-auto mb-3 text-brand" :size="34" />
          <p>Hozircha mos mahsulot topilmadi.</p>
        </div>
        <div v-else class="grid grid-cols-2 gap-3">
          <button
            v-for="product in filteredProducts"
            :key="product.id"
            class="product-card text-left"
            @click="openProduct(product)"
          >
            <div class="product-image">
              <img v-if="imageFor(product)" :src="imageFor(product)" :alt="product.name" />
              <ShoppingBag v-else :size="42" class="text-brand/50" />
              <span class="stock-pill">{{ product.quantity }} dona</span>
            </div>
            <div class="p-3">
              <p class="truncate text-sm font-bold">{{ product.name }}</p>
              <p class="mt-1 text-sm font-extrabold text-brand">{{ money(product.price) }}</p>
            </div>
          </button>
        </div>
      </div>

      <div v-else-if="view === 'orders'">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="section-title">Mening buyurtmalarim</h2>
          <button class="text-sm font-bold text-brand" @click="setView('shop')">Katalog</button>
        </div>
        <div v-if="!orders.length" class="empty-state">Hali buyurtmalar mavjud emas.</div>
        <article v-for="order in orders" :key="order.id" class="order-card">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-extrabold">Buyurtma #{{ order.id }}</p>
              <p class="mt-1 text-xs text-[var(--tg-hint)]">{{ new Date(order.created_at).toLocaleString('uz-UZ') }}</p>
            </div>
            <span class="status-pill" :class="`status-${order.status}`">{{ statusLabel(order.status) }}</span>
          </div>
          <p class="mt-4 text-lg font-black">{{ money(order.total_price) }}</p>
          <p v-if="order.comment" class="mt-2 text-sm text-[var(--tg-hint)]">💬 {{ order.comment }}</p>
        </article>
      </div>

      <div v-else-if="view === 'admin' && user?.is_admin">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <p class="text-sm text-[var(--tg-hint)]">Boshqaruv</p>
            <h2 class="section-title">Admin panel</h2>
          </div>
          <button class="secondary-button" @click="setView('shop')">Do‘kon</button>
        </div>

        <button class="primary-button mb-5 w-full" @click="showAdminForm = !showAdminForm">
          <Plus :size="18" /> Mahsulot qo‘shish
        </button>
        <form v-if="showAdminForm" class="panel mb-5 space-y-3" @submit.prevent="submitProduct">
          <input v-model="newProduct.name" class="input" required placeholder="Nom" />
          <textarea v-model="newProduct.description" class="input min-h-20" placeholder="Tavsif" />
          <div class="grid grid-cols-2 gap-3">
            <input v-model.number="newProduct.price" class="input" required min="0" type="number" placeholder="Narx" />
            <input v-model.number="newProduct.quantity" class="input" required min="0" type="number" placeholder="Qoldiq" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <select v-model="newProduct.category" class="input">
              <option value="suvenir">Suvenir</option>
              <option value="hudi">Xudi</option>
              <option value="futbolka">Futbolka</option>
            </select>
            <input v-model="newProduct.image_url" class="input" placeholder="Rasm URL (yoki fayl tanlang)" />
          </div>
          <input class="input" type="file" accept="image/*" @change="chooseImage" />
          <input v-model="newProduct.sizes" class="input" placeholder="O‘lchamlar: S, M, L, XL" />
          <input v-model="newProduct.colors" class="input" placeholder="Ranglar: Oq, Qora" />
          <button class="primary-button w-full" type="submit">Saqlash</button>
        </form>

        <h3 class="subheading">Yangi buyurtmalar</h3>
        <div v-if="!adminOrders.length" class="empty-state mb-5">Yangi buyurtmalar yo‘q.</div>
        <article v-for="order in adminOrders" :key="order.id" class="order-card mb-3">
          <div class="flex justify-between gap-3">
            <div>
              <p class="font-extrabold">#{{ order.id }} · {{ order.user_name || order.user_id }}</p>
              <p class="text-sm text-[var(--tg-hint)]">{{ order.phone_number }}</p>
            </div>
            <b>{{ money(order.total_price) }}</b>
          </div>
          <p class="mt-3 text-sm">{{ order.items?.map((item) => `${item.product_name} × ${item.quantity}`).join(', ') }}</p>
          <div class="mt-4 grid grid-cols-2 gap-2">
            <button class="success-button" @click="updateOrder(order.id, 'approve')">Qabul qilish</button>
            <button class="danger-button" @click="updateOrder(order.id, 'reject')">Rad etish</button>
          </div>
        </article>

        <h3 class="subheading mt-6">Mahsulotlar</h3>
        <article v-for="product in adminProducts" :key="product.id" class="admin-product">
          <div>
            <p class="font-bold">{{ product.name }}</p>
            <p class="text-sm text-[var(--tg-hint)]">{{ product.quantity }} dona · {{ money(product.price) }}</p>
          </div>
          <button class="secondary-button" @click="openStock(product)">+ Kirim</button>
        </article>
      </div>
    </section>

    <nav class="bottom-nav">
      <button :class="{ 'nav-active': view === 'shop' }" @click="setView('shop')">
        <ShoppingBag :size="20" /> <span>Do‘kon</span>
      </button>
      <button :class="{ 'nav-active': view === 'orders' }" @click="setView('orders')">
        <ClipboardList :size="20" /> <span>Buyurtmalar</span>
      </button>
      <button v-if="user?.is_admin" :class="{ 'nav-active': view === 'admin' }" @click="setView('admin')">
        <ShieldCheck :size="20" /> <span>Admin</span>
      </button>
    </nav>

    <div v-if="selected" class="modal-backdrop" @click.self="selected = null">
      <article class="modal-card">
        <button class="modal-close" @click="selected = null"><X :size="20" /></button>
        <div class="product-image large">
          <img v-if="imageFor(selected)" :src="imageFor(selected)" :alt="selected.name" />
          <ShoppingBag v-else :size="60" class="text-brand/50" />
        </div>
        <div class="p-5">
          <p class="text-xs font-bold uppercase tracking-widest text-brand">{{ categoryLabel(selected.category) }}</p>
          <h2 class="mt-2 text-2xl font-black">{{ selected.name }}</h2>
          <p class="mt-2 text-sm leading-6 text-[var(--tg-hint)]">{{ selected.description }}</p>
          <div v-if="selected.sizes?.length" class="mt-5">
            <p class="mb-2 text-sm font-bold">O‘lcham</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="size in selected.sizes"
                :key="size"
                class="chip"
                :class="{ 'chip-active': selectedSize === size }"
                @click="selectedSize = size"
              >
                {{ size }}
              </button>
            </div>
          </div>
          <div v-if="selected.colors?.length" class="mt-4">
            <p class="mb-2 text-sm font-bold">Rang</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="color in selected.colors"
                :key="color"
                class="chip"
                :class="{ 'chip-active': selectedColor === color }"
                @click="selectedColor = color"
              >
                {{ color }}
              </button>
            </div>
          </div>
          <div class="my-5 flex items-center justify-between">
            <span class="text-xl font-black text-brand">{{ money(selected.price) }}</span>
            <span class="text-sm text-[var(--tg-hint)]">{{ selected.quantity }} dona qoldi</span>
          </div>
          <button class="primary-button w-full" @click="addProduct(selected, selectedSize, selectedColor)">
            <ShoppingCart :size="18" /> Savatga qo‘shish
          </button>
        </div>
      </article>
    </div>

    <div v-if="cartOpen" class="modal-backdrop" @click.self="cartOpen = false">
      <article class="modal-card p-5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-black">Savat</h2>
          <button class="icon-button" @click="cartOpen = false"><X :size="19" /></button>
        </div>
        <div v-if="!cart.length" class="empty-state">Savat bo‘sh.</div>
        <div v-else>
          <div
            v-for="line in cart"
            :key="`${line.product.id}-${line.size}-${line.color}`"
            class="cart-line"
          >
            <div class="min-w-0 flex-1">
              <p class="truncate font-bold">{{ line.product.name }}</p>
              <p class="mt-1 text-sm font-bold text-brand">{{ money(line.product.price * line.quantity) }}</p>
              <p v-if="line.size || line.color" class="text-xs text-[var(--tg-hint)]">
                {{ [line.size, line.color].filter(Boolean).join(' · ') }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button class="quantity-button" @click="decrement(line)"><Minus :size="15" /></button>
              <span class="w-5 text-center font-bold">{{ line.quantity }}</span>
              <button class="quantity-button" @click="increment(line)"><Plus :size="15" /></button>
              <button class="ml-1 text-red-500" @click="removeLine(line)"><Trash2 :size="17" /></button>
            </div>
          </div>
          <div class="mt-5 border-t border-slate-200 pt-4">
            <div class="mb-3 flex justify-between text-lg font-black">
              <span>Jami</span><span class="text-brand">{{ money(cartTotal) }}</span>
            </div>
            <button class="primary-button w-full" @click="openCheckout">Rasmiylashtirish</button>
          </div>
        </div>
      </article>
    </div>

    <div v-if="checkoutOpen" class="modal-backdrop" @click.self="checkoutOpen = false">
      <article class="modal-card p-5">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-black">Buyurtmani rasmiylashtirish</h2>
          <button class="icon-button" @click="checkoutOpen = false"><X :size="19" /></button>
        </div>
        <div class="mb-5 space-y-2">
          <div v-for="line in cart" :key="`${line.product.id}-${line.size}-${line.color}`" class="flex justify-between text-sm">
            <span>{{ line.product.name }} × {{ line.quantity }}</span>
            <b>{{ money(line.product.price * line.quantity) }}</b>
          </div>
          <div class="border-t border-slate-200 pt-3 text-lg font-black">Jami: {{ money(cartTotal) }}</div>
        </div>
        <input v-model="phone" class="input mb-3" type="tel" inputmode="tel" placeholder="+998 90 123 45 67" />
        <textarea v-model="comment" class="input mb-4 min-h-20" placeholder="Izoh (ixtiyoriy)" />
        <button class="primary-button w-full" :disabled="submitting" @click="submitOrder">
          {{ submitting ? 'Yuborilmoqda...' : 'Buyurtmani tasdiqlash' }}
        </button>
      </article>
    </div>

    <div v-if="stockProduct" class="modal-backdrop" @click.self="stockProduct = null">
      <form class="modal-card p-5" @submit.prevent="submitStock">
        <div class="mb-5 flex items-center justify-between">
          <h2 class="text-xl font-black">Kirim: {{ stockProduct.name }}</h2>
          <button type="button" class="icon-button" @click="stockProduct = null"><X :size="19" /></button>
        </div>
        <input v-model.number="stockQuantity" class="input mb-3" type="number" min="1" required placeholder="Miqdor" />
        <input v-model="stockComment" class="input mb-4" placeholder="Izoh" />
        <button class="primary-button w-full" type="submit">Kirimni saqlash</button>
      </form>
    </div>

    <button v-if="view !== 'shop' && !checkoutOpen" class="floating-back" @click="setView('shop')">
      <ChevronLeft :size="19" /> Katalog
    </button>
    <div v-if="toast" class="toast">{{ toast }}</div>
  </main>
</template>
