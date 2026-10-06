from aiogram.types import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  KeyboardButton,
  ReplyKeyboardMarkup,
  WebAppInfo,
)

from config import WEBAPP_URL
from supabase_db import format_price, get_all_products, get_orders_by_status

# Reply tugmalar
BTN_CATALOG = "🛍 Katalog"
BTN_CART = "🛒 Savat"
BTN_MY_ORDERS = "📦 Mening buyurtmalarim"
BTN_ABOUT = "ℹ️ Biz haqimizda"

BTN_ADD_PRODUCT = "➕ Mahsulot qo'shish"
BTN_STOCK_IN = "📥 Kirim qilish"
BTN_MANAGE = "✏️ Mahsulotlarni boshqarish"
BTN_NEW_ORDERS = "📋 Yangi buyurtmalar"
BTN_STATS = "📊 Statistika"
BTN_CLIENT_MENU = "🛍 Mijoz menyusi"
BTN_ADMIN_MENU = "⚙️ Admin menyu"
BTN_CANCEL = "❌ Bekor qilish"


def client_reply_keyboard(show_admin_back: bool = False) -> ReplyKeyboardMarkup:
  rows = [
    [KeyboardButton(text=BTN_CATALOG), KeyboardButton(text=BTN_CART)],
    [KeyboardButton(text=BTN_MY_ORDERS), KeyboardButton(text=BTN_ABOUT)],
  ]
  if WEBAPP_URL:
    rows.insert(
      0,
      [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
    )
  if show_admin_back:
    rows.append([KeyboardButton(text=BTN_ADMIN_MENU)])
  return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_reply_keyboard() -> ReplyKeyboardMarkup:
  rows = [
      [KeyboardButton(text=BTN_ADD_PRODUCT), KeyboardButton(text=BTN_STOCK_IN)],
      [KeyboardButton(text=BTN_MANAGE), KeyboardButton(text=BTN_NEW_ORDERS)],
      [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_CLIENT_MENU)],
  ]
  if WEBAPP_URL:
    rows.insert(
      0,
      [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
    )
  return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def role_reply_keyboard(is_admin_user: bool) -> ReplyKeyboardMarkup:
  return admin_reply_keyboard() if is_admin_user else client_reply_keyboard()


def cancel_reply_keyboard() -> ReplyKeyboardMarkup:
  return ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
    resize_keyboard=True,
  )


def catalog_keyboard(products: list[dict]) -> InlineKeyboardMarkup:
  buttons: list[list[InlineKeyboardButton]] = []
  for product in products:
    label = f"{product['name']} — {format_price(product['price'])}"
    buttons.append(
      [
        InlineKeyboardButton(
          text=label,
          callback_data=f"client:product:{product['id']}",
        )
      ]
    )
  if not buttons:
    buttons.append(
      [InlineKeyboardButton(text="Mahsulotlar yo'q", callback_data="noop")]
    )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_buy_keyboard(product_id: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="🛒 Savatga qo'shish",
          callback_data=f"client:addcart:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text="⚡️ Tezkor buyurtma",
          callback_data=f"client:buynow:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text="◀️ Katalog",
          callback_data="client:catalog",
        )
      ],
    ]
  )


def cart_keyboard(has_items: bool) -> InlineKeyboardMarkup:
  rows: list[list[InlineKeyboardButton]] = []
  if has_items:
    rows.append(
      [
        InlineKeyboardButton(
          text="✅ Buyurtma berish",
          callback_data="client:checkout",
        )
      ]
    )
    rows.append(
      [
        InlineKeyboardButton(
          text="🗑 Savatni tozalash",
          callback_data="client:clearcart",
        )
      ]
    )
  rows.append(
    [
      InlineKeyboardButton(
        text="🛍 Katalogga",
        callback_data="client:catalog",
      )
    ]
  )
  return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_inline_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="client:cancel")]
    ]
  )


def admin_products_keyboard(action: str) -> InlineKeyboardMarkup:
  products = get_all_products(include_inactive=True)
  buttons: list[list[InlineKeyboardButton]] = []
  for product in products:
    status = "✅" if product["is_active"] else "🗄"
    buttons.append(
      [
        InlineKeyboardButton(
          text=f"{status} {product['name']} ({product['quantity']})",
          callback_data=f"admin:{action}:{product['id']}",
        )
      ]
    )
  if not buttons:
    buttons.append(
      [InlineKeyboardButton(text="Mahsulotlar yo'q", callback_data="noop")]
    )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_manage_item_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
  archive_text = "🗄 Arxivlash" if is_active else "♻️ Faollashtirish"
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="💰 Narxni o'zgartirish",
          callback_data=f"admin:editprice:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text=archive_text,
          callback_data=f"admin:toggle:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text="🗑 O'chirish",
          callback_data=f"admin:delete:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text="◀️ Ro'yxat",
          callback_data="admin:manage",
        )
      ],
    ]
  )


def admin_orders_keyboard() -> InlineKeyboardMarkup:
  orders = get_orders_by_status("pending")
  buttons: list[list[InlineKeyboardButton]] = []
  for order in orders:
    label = (
      f"#{order['id']} — {format_price(order['total_price'])} "
      f"({order.get('user_name') or order['user_id']})"
    )
    buttons.append(
      [
        InlineKeyboardButton(
          text=label,
          callback_data=f"admin:order:{order['id']}",
        )
      ]
    )
  if not buttons:
    buttons.append(
      [
        InlineKeyboardButton(
          text="Yangi buyurtmalar yo'q",
          callback_data="noop",
        )
      ]
    )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_order_actions_keyboard(order_id: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="✅ Qabul qilish",
          callback_data=f"admin:approve:{order_id}",
        ),
        InlineKeyboardButton(
          text="❌ Rad etish",
          callback_data=f"admin:reject:{order_id}",
        ),
      ],
      [
        InlineKeyboardButton(
          text="◀️ Ro'yxat",
          callback_data="admin:orders",
        )
      ],
    ]
  )
