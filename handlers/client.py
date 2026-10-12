from html import escape

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from supabase_db import (
  add_to_cart,
  cart_details,
  clear_cart,
  create_order,
  format_price,
  get_active_products,
  get_product,
  get_user_language,
)
from filters.admin import is_admin
from keyboards import (
  cancel_inline_keyboard,
  cancel_reply_keyboard,
  cart_keyboard,
  catalog_keyboard,
  client_reply_keyboard,
  pay_order_keyboard,
  phone_request_keyboard,
  product_buy_keyboard,
)
from locales import button_values, t
from states import OrderStates
from utils.media import replace_with_text, send_product_card

router = Router(name="client")

_ORDER_STATES = {
  OrderStates.waiting_quantity.state,
  OrderStates.waiting_phone.state,
}


def _client_kb(user_id: int, lang: str):
  return client_reply_keyboard(show_admin_back=is_admin(user_id), lang=lang)


def _share(lang: str) -> str:
  return t(lang, "btn_share_phone")


def _normalize_phone(text: str) -> str | None:
  cleaned = (
    text.strip()
    .replace(" ", "")
    .replace("-", "")
    .replace("(", "")
    .replace(")", "")
  )
  if cleaned.startswith("+"):
    digits = cleaned[1:]
  else:
    digits = cleaned
  if digits.isdigit() and 9 <= len(digits) <= 15:
    return cleaned if cleaned.startswith("+") else cleaned
  return None


async def _block_if_ordering(message: Message, state: FSMContext, lang: str) -> bool:
  current = await state.get_state()
  if current not in _ORDER_STATES:
    return False
  await message.answer(
    t(lang, "ordering_busy", cancel=t(lang, "btn_cancel")),
    reply_markup=phone_request_keyboard(lang)
    if current == OrderStates.waiting_phone.state
    else cancel_reply_keyboard(lang),
  )
  return True


# ── Reply menyu ────────────────────────────────────────────


@router.message(F.text.in_(button_values("btn_catalog")))
async def show_catalog(message: Message, state: FSMContext, lang: str) -> None:
  if await _block_if_ordering(message, state, lang):
    return
  await state.clear()
  products = get_active_products()
  await message.answer(
    t(lang, "catalog_title"),
    reply_markup=_client_kb(message.from_user.id, lang),
  )
  if not products:
    await message.answer(t(lang, "catalog_empty"))
    return
  await message.answer(
    t(lang, "catalog_pick"),
    reply_markup=catalog_keyboard(products, lang),
  )


@router.message(F.text.in_(button_values("btn_cart")))
async def show_cart(message: Message, state: FSMContext, lang: str) -> None:
  if await _block_if_ordering(message, state, lang):
    return
  await state.clear()
  await _send_cart(message, message.from_user.id, lang)


@router.message(OrderStates.waiting_quantity, F.text.in_(button_values("btn_cancel")))
@router.message(OrderStates.waiting_phone, F.text.in_(button_values("btn_cancel")))
async def cancel_order_flow(message: Message, state: FSMContext, lang: str) -> None:
  await state.clear()
  await message.answer(
    t(lang, "order_cancelled"),
    reply_markup=_client_kb(message.from_user.id, lang),
  )


# ── Inline: katalog / mahsulot ─────────────────────────────


@router.callback_query(F.data == "client:catalog")
async def cb_catalog(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  await state.clear()
  await callback.answer()
  products = get_active_products()
  if not products:
    await replace_with_text(callback.message, t(lang, "catalog_empty"))
    return
  await replace_with_text(
    callback.message,
    t(lang, "catalog_body"),
    catalog_keyboard(products, lang),
  )


@router.callback_query(F.data.startswith("client:product:"))
async def cb_product(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  await state.clear()
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer(t(lang, "product_unavailable"), show_alert=True)
    return
  await callback.answer()
  await send_product_card(
    callback.message,
    product,
    product_buy_keyboard(product_id, lang),
  )


@router.callback_query(F.data.startswith("client:addtocart1:"))
async def cb_add_cart_one(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer(t(lang, "product_unavailable"), show_alert=True)
    return
  add_to_cart(callback.from_user.id, product_id, 1)
  await callback.answer(t(lang, "added_toast"))
  await state.clear()
  await callback.message.answer(
    t(
      lang,
      "added_hint",
      name=escape(str(product["name"])),
      cart=t(lang, "btn_cart"),
    ),
    reply_markup=_client_kb(callback.from_user.id, lang),
  )


@router.callback_query(F.data.startswith("client:buy1:"))
async def cb_buy_one(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer(t(lang, "product_unavailable"), show_alert=True)
    return
  await callback.answer()
  await state.set_state(OrderStates.waiting_phone)
  await state.update_data(mode="buynow", product_id=product_id, buynow_qty=1)
  await callback.message.answer(
    t(
      lang,
      "order_line",
      name=escape(str(product["name"])),
      qty=1,
      price=format_price(product["price"]),
    ),
    reply_markup=phone_request_keyboard(lang),
  )


@router.callback_query(F.data.startswith("client:addcart:"))
async def cb_add_cart(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer(t(lang, "product_unavailable"), show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_quantity)
  await state.update_data(mode="cart", product_id=product_id)
  await replace_with_text(
    callback.message,
    t(
      lang,
      "stock_left",
      name=escape(str(product["name"])),
      qty=product["quantity"],
    ),
    cancel_inline_keyboard(lang),
  )


@router.callback_query(F.data.startswith("client:buynow:"))
async def cb_buy_now(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer(t(lang, "product_unavailable"), show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_quantity)
  await state.update_data(mode="buynow", product_id=product_id)
  await replace_with_text(
    callback.message,
    t(
      lang,
      "buy_qty_prompt",
      name=escape(str(product["name"])),
      qty=product["quantity"],
    ),
    cancel_inline_keyboard(lang),
  )


@router.message(OrderStates.waiting_quantity, F.text)
async def process_quantity(message: Message, state: FSMContext, lang: str) -> None:
  text = (message.text or "").strip()
  if not text.isdigit() or int(text) <= 0:
    await message.answer(
      t(lang, "bad_qty"),
      reply_markup=cancel_reply_keyboard(lang),
    )
    return

  quantity = int(text)
  data = await state.get_data()
  product_id = data.get("product_id")
  mode = data.get("mode")
  product = get_product(product_id) if product_id else None

  if not product or not product["is_active"]:
    await state.clear()
    await message.answer(
      t(lang, "product_missing"),
      reply_markup=_client_kb(message.from_user.id, lang),
    )
    return

  if quantity > product["quantity"]:
    await message.answer(
      t(lang, "not_enough_stock", qty=product["quantity"]),
      reply_markup=cancel_reply_keyboard(lang),
    )
    return

  if mode == "cart":
    add_to_cart(message.from_user.id, product_id, quantity)
    await state.clear()
    await message.answer(
      t(lang, "added_named", name=escape(str(product["name"])), qty=quantity),
      reply_markup=_client_kb(message.from_user.id, lang),
    )
    await _send_cart(message, message.from_user.id, lang)
    return

  await state.update_data(buynow_qty=quantity)
  await state.set_state(OrderStates.waiting_phone)
  await message.answer(
    t(lang, "ask_phone", share=_share(lang)),
    reply_markup=phone_request_keyboard(lang),
  )


@router.callback_query(F.data == "client:clearcart")
async def cb_clear_cart(callback: CallbackQuery, lang: str) -> None:
  clear_cart(callback.from_user.id)
  await callback.answer(t(lang, "cart_cleared_toast"))
  await replace_with_text(
    callback.message,
    t(lang, "cart_empty_short"),
    cart_keyboard(False, lang),
  )


@router.callback_query(F.data == "client:checkout")
async def cb_checkout(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  items, total = cart_details(callback.from_user.id)
  if not items:
    await callback.answer(t(lang, "cart_empty_alert"), show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_phone)
  await state.update_data(mode="cart_checkout")
  await callback.message.answer(
    t(
      lang,
      "checkout_intro",
      total=format_price(total),
      count=len(items),
      share=_share(lang),
    ),
    reply_markup=phone_request_keyboard(lang),
  )


async def _notify_admins(bot, text_key: str, **kwargs: object) -> None:
  for admin_id in ADMIN_IDS:
    try:
      admin_lang = await asyncio.to_thread(get_user_language, admin_id)
      await bot.send_message(admin_id, t(admin_lang, text_key, **kwargs))
    except Exception:
      pass


async def _finalize_order(message: Message, state: FSMContext, phone: str, lang: str) -> None:
  data = await state.get_data()
  mode = data.get("mode")
  user = message.from_user
  user_name = user.full_name or user.username or str(user.id)

  order_items: list[dict] = []
  is_buynow = mode == "buynow" or (
    mode != "cart_checkout" and bool(data.get("buynow_qty"))
  )

  if is_buynow:
    product_id = data.get("product_id")
    qty = data.get("buynow_qty")
    product = get_product(product_id) if product_id else None
    if not product or not qty:
      await state.clear()
      await message.answer(
        t(lang, "restart_error"),
        reply_markup=_client_kb(user.id, lang),
      )
      return
    if product["quantity"] < qty:
      await state.clear()
      await message.answer(
        t(lang, "stock_short", qty=product["quantity"]),
        reply_markup=_client_kb(user.id, lang),
      )
      return
    order_items = [
      {
        "product_id": product_id,
        "quantity": qty,
        "unit_price": product["price"],
      }
    ]
  else:
    details, _total = cart_details(user.id)
    if not details:
      await state.clear()
      await message.answer(
        t(lang, "cart_empty_long"),
        reply_markup=_client_kb(user.id, lang),
      )
      return
    order_items = [
      {
        "product_id": row["product"]["id"],
        "quantity": row["quantity"],
        "unit_price": row["product"]["price"],
      }
      for row in details
    ]

  try:
    order = create_order(user.id, user_name, phone, order_items)
  except Exception as error:
    await state.clear()
    await message.answer(
      t(lang, "order_failed_error", error=escape(str(error))),
      reply_markup=_client_kb(user.id, lang),
    )
    return

  await state.clear()

  if not order:
    await message.answer(
      t(lang, "order_failed_stock"),
      reply_markup=_client_kb(user.id, lang),
    )
    return

  if not is_buynow:
    clear_cart(user.id)

  await message.answer(
    t(
      lang,
      "order_created",
      order_id=order["id"],
      rows=len(order_items),
      total=format_price(order["total_price"]),
      phone=escape(phone),
    ),
    reply_markup=_client_kb(user.id, lang),
  )

  from handlers.payment import available_providers, send_order_invoice

  order_id = int(order["id"])
  providers = available_providers()
  try:
    if len(providers) == 1:
      code, label = providers[0]
      sent = await send_order_invoice(
        message.bot,
        message.chat.id,
        order,
        provider=code,
        intro_text=t(lang, "pay_finish", label=label),
        lang=lang,
      )
      if not sent:
        await message.answer(
          t(lang, "invoice_not_opened"),
          reply_markup=pay_order_keyboard(order_id, lang),
        )
    elif providers:
      await message.answer(
        t(lang, "choose_payment"),
        reply_markup=pay_order_keyboard(order_id, lang),
      )
    else:
      await message.answer(
        t(lang, "payments_off"),
        reply_markup=_client_kb(user.id, lang),
      )
  except Exception as error:
    await message.answer(
      t(lang, "invoice_saved_failed", error=escape(str(error))),
      reply_markup=pay_order_keyboard(order_id, lang),
    )

  await _notify_admins(
    message.bot,
    "admin_new_order",
    order_id=order["id"],
    name=escape(user_name),
    phone=escape(phone),
    rows=len(order_items),
    total=format_price(order["total_price"]),
  )


@router.message(OrderStates.waiting_phone, F.contact)
async def process_phone_contact(message: Message, state: FSMContext, lang: str) -> None:
  contact = message.contact
  if not contact or not contact.phone_number:
    await message.answer(
      t(lang, "phone_missing"),
      reply_markup=phone_request_keyboard(lang),
    )
    return
  phone = contact.phone_number.strip()
  if not phone.startswith("+"):
    phone = f"+{phone}"
  normalized = _normalize_phone(phone)
  if not normalized:
    await message.answer(
      t(lang, "phone_bad"),
      reply_markup=phone_request_keyboard(lang),
    )
    return
  await _finalize_order(message, state, normalized, lang)


@router.message(OrderStates.waiting_phone, F.text)
async def process_phone(message: Message, state: FSMContext, lang: str) -> None:
  phone = _normalize_phone(message.text or "")
  if not phone:
    await message.answer(
      t(lang, "phone_bad_share", share=_share(lang)),
      reply_markup=phone_request_keyboard(lang),
    )
    return
  await _finalize_order(message, state, phone, lang)


@router.callback_query(F.data == "client:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
  await state.clear()
  await callback.answer(t(lang, "cancelled"))
  await replace_with_text(callback.message, t(lang, "cancelled"))


@router.message(OrderStates.waiting_quantity)
async def quantity_hint(message: Message, lang: str) -> None:
  await message.answer(
    t(lang, "qty_hint"),
    reply_markup=cancel_reply_keyboard(lang),
  )


@router.message(OrderStates.waiting_phone)
async def phone_hint(message: Message, lang: str) -> None:
  await message.answer(
    t(lang, "phone_hint", share=_share(lang)),
    reply_markup=phone_request_keyboard(lang),
  )


async def _send_cart(message: Message, user_id: int, lang: str) -> None:
  items, total = cart_details(user_id)
  await message.answer(
    t(lang, "cart_title"),
    reply_markup=_client_kb(user_id, lang),
  )
  if not items:
    await message.answer(
      t(lang, "cart_empty_hint"),
      reply_markup=cart_keyboard(False, lang),
    )
    return

  lines = []
  for row in items:
    product = row["product"]
    lines.append(
      f"• {escape(str(product['name']))} × {row['quantity']} = "
      f"{format_price(row['line_total'])}"
    )
  lines.append(t(lang, "cart_total", total=format_price(total)))
  await message.answer(
    "\n".join(lines),
    reply_markup=cart_keyboard(True, lang),
  )
