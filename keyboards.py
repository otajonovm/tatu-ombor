from aiogram.types import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  KeyboardButton,
  ReplyKeyboardMarkup,
  WebAppInfo,
)

from config import CLICK_PROVIDER_TOKEN, PAYME_PROVIDER_TOKEN, WEBAPP_URL
from locales import t
from supabase_db import format_price, get_all_products, get_orders_by_status

# Reply tugmalar
BTN_CATALOG = "🛍 Katalog"
BTN_CART = "🛒 Savat"
BTN_MY_ORDERS = "📦 Mening buyurtmalarim"
BTN_PICKUP = "📍 Qayerdan olib ketaman?"

BTN_ADD_PRODUCT = "➕ Mahsulot qo'shish"
BTN_STOCK_IN = "📥 Kirim qilish"
BTN_MANAGE = "✏️ Mahsulotlarni boshqarish"
BTN_NEW_ORDERS = "📋 Yangi buyurtmalar"
BTN_STATS = "📊 Statistika"
BTN_CLIENT_MENU = "🛍 Mijoz menyusi"
BTN_ADMIN_MENU = "⚙️ Admin menyu"
BTN_CANCEL = "❌ Bekor qilish"


def language_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
      ]
    ]
  )


def client_reply_keyboard(
  show_admin_back: bool = False,
  lang: str = "uz",
) -> ReplyKeyboardMarkup:
  rows = [
    [
      KeyboardButton(text=t(lang, "btn_catalog")),
      KeyboardButton(text=t(lang, "btn_cart")),
    ],
    [KeyboardButton(text=t(lang, "btn_orders"))],
    [
      KeyboardButton(text=t(lang, "btn_pickup")),
      KeyboardButton(text=t(lang, "btn_language")),
    ],
  ]
  if WEBAPP_URL:
    rows.insert(
      0,
      [
        KeyboardButton(
          text=t(lang, "btn_open_shop"),
          web_app=WebAppInfo(url=WEBAPP_URL),
        )
      ],
    )
  if show_admin_back:
    rows.append([KeyboardButton(text=t(lang, "btn_admin_menu"))])
  return ReplyKeyboardMarkup(
    keyboard=rows,
    resize_keyboard=True,
    is_persistent=True,
  )


def admin_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
  rows = [
      [KeyboardButton(text=BTN_ADD_PRODUCT), KeyboardButton(text=BTN_STOCK_IN)],
      [KeyboardButton(text=BTN_MANAGE), KeyboardButton(text=BTN_NEW_ORDERS)],
      [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_CLIENT_MENU)],
      [KeyboardButton(text=t(lang, "btn_language"))],
  ]
  if WEBAPP_URL:
    rows.insert(
      0,
      [KeyboardButton(text="🛍 Do'konni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
    )
  return ReplyKeyboardMarkup(
    keyboard=rows,
    resize_keyboard=True,
    is_persistent=True,
  )


def role_reply_keyboard(is_admin_user: bool, lang: str = "uz") -> ReplyKeyboardMarkup:
  if is_admin_user:
    return admin_reply_keyboard(lang)
  return client_reply_keyboard(lang=lang)


def cancel_reply_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
  return ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=t(lang, "btn_cancel"))]],
    resize_keyboard=True,
    is_persistent=True,
  )


def catalog_keyboard(products: list[dict], lang: str = "uz") -> InlineKeyboardMarkup:
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
      [InlineKeyboardButton(text=t(lang, "btn_no_products"), callback_data="noop")]
    )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_buy_keyboard(product_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text=t(lang, "btn_add_one"),
          callback_data=f"client:addtocart1:{product_id}",
        ),
        InlineKeyboardButton(
          text=t(lang, "btn_buy_one"),
          callback_data=f"client:buy1:{product_id}",
        ),
      ],
      [
        InlineKeyboardButton(
          text=t(lang, "btn_add_qty"),
          callback_data=f"client:addcart:{product_id}",
        ),
        InlineKeyboardButton(
          text=t(lang, "btn_buy_qty"),
          callback_data=f"client:buynow:{product_id}",
        ),
      ],
      [
        InlineKeyboardButton(
          text=t(lang, "btn_back_catalog"),
          callback_data="client:catalog",
        )
      ],
    ]
  )


def phone_request_keyboard(lang: str = "uz") -> ReplyKeyboardMarkup:
  return ReplyKeyboardMarkup(
    keyboard=[
      [KeyboardButton(text=t(lang, "btn_share_phone"), request_contact=True)],
      [KeyboardButton(text=t(lang, "btn_cancel"))],
    ],
    resize_keyboard=True,
    is_persistent=True,
  )


def pay_order_keyboard(order_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
  """Click va Payme — ikkalasi ham yoqilgan bo'lsa, mijoz o'zi tanlaydi."""
  rows: list[list[InlineKeyboardButton]] = []
  if CLICK_PROVIDER_TOKEN:
    rows.append(
      [
        InlineKeyboardButton(
          text=t(lang, "btn_pay_click"),
          callback_data=f"client:pay:{order_id}:click",
        )
      ]
    )
  if PAYME_PROVIDER_TOKEN:
    rows.append(
      [
        InlineKeyboardButton(
          text=t(lang, "btn_pay_payme"),
          callback_data=f"client:pay:{order_id}:payme",
        )
      ]
    )
  return InlineKeyboardMarkup(inline_keyboard=rows)


def cart_keyboard(has_items: bool, lang: str = "uz") -> InlineKeyboardMarkup:
  rows: list[list[InlineKeyboardButton]] = []
  if has_items:
    rows.append(
      [
        InlineKeyboardButton(
          text=t(lang, "btn_checkout"),
          callback_data="client:checkout",
        )
      ]
    )
    rows.append(
      [
        InlineKeyboardButton(
          text=t(lang, "btn_clear_cart"),
          callback_data="client:clearcart",
        )
      ]
    )
  rows.append(
    [
      InlineKeyboardButton(
        text=t(lang, "btn_to_catalog"),
        callback_data="client:catalog",
      )
    ]
  )
  return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text=t(lang, "btn_cancel"),
          callback_data="client:cancel",
        )
      ]
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


def admin_qr_keyboard(product_id: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="🔲 QR Kod yaratish",
          callback_data=f"admin:qr:{product_id}",
        )
      ]
    ]
  )


def admin_manage_item_keyboard(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
  archive_text = "🗄 Arxivlash" if is_active else "♻️ Faollashtirish"
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="🔲 QR Kod yaratish",
          callback_data=f"admin:qr:{product_id}",
        )
      ],
      [
        InlineKeyboardButton(
          text="✏️ Nom",
          callback_data=f"admin:editname:{product_id}",
        ),
        InlineKeyboardButton(
          text="🖼 Rasm",
          callback_data=f"admin:editimage:{product_id}",
        ),
      ],
      [
        InlineKeyboardButton(
          text="📦 Miqdor",
          callback_data=f"admin:editqty:{product_id}",
        ),
        InlineKeyboardButton(
          text="💰 Narx",
          callback_data=f"admin:editprice:{product_id}",
        ),
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


def order_slip_keyboard(
  order_id: int,
  *,
  ready: bool,
  pending: bool,
  lang: str = "uz",
) -> InlineKeyboardMarkup:
  rows: list[list[InlineKeyboardButton]] = []
  if ready:
    rows.append(
      [
        InlineKeyboardButton(
          text=t(lang, "btn_qr"),
          callback_data=f"order:qr:{order_id}",
        )
      ]
    )
  if pending:
    rows.extend(pay_order_keyboard(order_id, lang).inline_keyboard)
  rows.append(
    [
      InlineKeyboardButton(
        text=t(lang, "btn_pickup"),
        callback_data="order:pickup",
      )
    ]
  )
  return InlineKeyboardMarkup(inline_keyboard=rows)


def deliver_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="✅ Mahsulotni topshirdim",
          callback_data=f"order:deliver:{order_id}",
        )
      ]
    ]
  )


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
