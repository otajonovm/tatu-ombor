from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from db import get_all_products


def main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
  buttons = [
    [
      InlineKeyboardButton(
        text="📦 Qoldiqni tekshirish",
        callback_data="action:check",
      )
    ],
    [
      InlineKeyboardButton(
        text="🎁 Sovg'a berish",
        callback_data="action:out",
      )
    ],
    [
      InlineKeyboardButton(
        text="➕ Kirim qilish",
        callback_data="action:in",
      )
    ],
    [
      InlineKeyboardButton(
        text="🏪 Ombor ro'yxati",
        callback_data="action:sklad",
      )
    ],
  ]

  if is_admin:
    buttons.append(
      [
        InlineKeyboardButton(
          text="⚙️ Admin panel",
          callback_data="admin:panel",
        )
      ]
    )

  return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(
  action: str,
  back_callback: str = "menu:main",
) -> InlineKeyboardMarkup:
  products = get_all_products()
  buttons: list[list[InlineKeyboardButton]] = []

  for product in products:
    label = f"{product['name']} ({product['quantity']} dona)"
    buttons.append(
      [
        InlineKeyboardButton(
          text=label,
          callback_data=f"product:{action}:{product['id']}",
        )
      ]
    )

  if not buttons:
    buttons.append(
      [
        InlineKeyboardButton(
          text="Mahsulotlar yo'q",
          callback_data="noop",
        )
      ]
    )

  buttons.append(
    [InlineKeyboardButton(text="◀️ Orqaga", callback_data=back_callback)]
  )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def sklad_keyboard() -> InlineKeyboardMarkup:
  products = get_all_products()
  buttons: list[list[InlineKeyboardButton]] = []

  for product in products:
    qty = product["quantity"]
    status = "✅" if qty > 10 else ("⚠️" if qty > 0 else "❌")
    buttons.append(
      [
        InlineKeyboardButton(
          text=f"{status} {product['name']} — {qty} dona",
          callback_data=f"detail:{product['id']}",
        )
      ]
    )

  buttons.append(
    [InlineKeyboardButton(text="◀️ Bosh menyu", callback_data="menu:main")]
  )
  return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="➕ Kirim qilish",
          callback_data=f"product:in:{product_id}",
        ),
        InlineKeyboardButton(
          text="🎁 Sovg'a berish",
          callback_data=f"product:out:{product_id}",
        ),
      ],
      [
        InlineKeyboardButton(
          text="◀️ Ombor ro'yxati",
          callback_data="action:sklad",
        )
      ],
    ]
  )


def gift_confirm_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="✅ Tasdiqlash",
          callback_data="confirm:gift",
        ),
        InlineKeyboardButton(
          text="❌ Bekor qilish",
          callback_data="menu:main",
        ),
      ]
    ]
  )


def confirm_keyboard(action: str, product_id: int, quantity: int) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="✅ Tasdiqlash",
          callback_data=f"confirm:{action}:{product_id}:{quantity}",
        ),
        InlineKeyboardButton(
          text="❌ Bekor qilish",
          callback_data="menu:main",
        ),
      ]
    ]
  )


def cancel_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="menu:main")]
    ]
  )


def admin_panel_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
    inline_keyboard=[
      [
        InlineKeyboardButton(
          text="➕ Mahsulot qo'shish",
          callback_data="admin:add_product",
        )
      ],
      [
        InlineKeyboardButton(
          text="🗑 Mahsulot o'chirish",
          callback_data="admin:delete_list",
        )
      ],
      [
        InlineKeyboardButton(
          text="📊 So'nggi harakatlar",
          callback_data="admin:history",
        )
      ],
      [
        InlineKeyboardButton(
          text="◀️ Bosh menyu",
          callback_data="menu:main",
        )
      ],
    ]
  )


def admin_delete_keyboard() -> InlineKeyboardMarkup:
  products = get_all_products()
  buttons: list[list[InlineKeyboardButton]] = []

  for product in products:
    buttons.append(
      [
        InlineKeyboardButton(
          text=f"🗑 {product['name']}",
          callback_data=f"admin:delete:{product['id']}",
        )
      ]
    )

  buttons.append(
    [InlineKeyboardButton(text="◀️ Admin panel", callback_data="admin:panel")]
  )
  return InlineKeyboardMarkup(inline_keyboard=buttons)
