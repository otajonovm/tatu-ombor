"""Olib ketish: mijoz kartasi, QR va 480-xona tasdig'i."""

from __future__ import annotations

import asyncio
import logging
import re
from html import escape

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import PICKUP_CONTACT, PICKUP_PHONE
from filters.admin import IsAdminFilter, is_admin
from keyboards import (
  cancel_reply_keyboard,
  client_reply_keyboard,
  deliver_order_keyboard,
  order_slip_keyboard,
  phone_request_keyboard,
  role_reply_keyboard,
)
from locales import button_values, t
from states import OrderStates
from services.qr import build_claim_qr_png
from supabase_db import (
  format_price,
  get_order,
  get_order_items,
  get_product,
  get_user_language,
  get_user_orders,
  mark_order_delivered,
)

logger = logging.getLogger(__name__)
router = Router(name="orders")

READY_STATUSES = {"paid", "approved"}
ACTIVE_STATUSES = READY_STATUSES | {"pending"}
ORDER_CODE_RE = re.compile(r"(?i)^(?:#?\s*tatu[-\s]*)?(\d{1,9})$")


def parse_claim_arg(args: str | None) -> int | None:
  """start=claim_42 → 42."""
  if not args:
    return None
  raw = args.strip()
  if not raw.lower().startswith("claim_"):
    return None
  order_id = raw.split("_", 1)[1].strip()
  if not order_id.isdigit():
    return None
  return int(order_id)


def parse_order_code(text: str | None) -> int | None:
  """#TATU-42, TATU-42 yoki 42."""
  if not text:
    return None
  match = ORDER_CODE_RE.fullmatch(text.strip())
  if not match:
    return None
  return int(match.group(1))


def order_code(order_id: int) -> str:
  return f"#TATU-{int(order_id)}"


def _client_kb(user_id: int, lang: str = "uz"):
  return client_reply_keyboard(show_admin_back=is_admin(user_id), lang=lang)


def _status_label(lang: str, status: str) -> str:
  key = f"status_{status}"
  label = t(lang, key)
  return status if label == key else label


async def _order_bundle(order_id: int) -> tuple[dict | None, list[dict]]:
  order = await asyncio.to_thread(get_order, order_id)
  if not order:
    return None, []
  items = await asyncio.to_thread(get_order_items, order_id)
  return order, items


def _product_lines(items: list[dict], lang: str) -> str:
  if not items:
    return "—"
  return "\n".join(
    t(
      lang,
      "slip_product",
      name=escape(str(row.get("product_name") or t(lang, "product_fallback"))),
      qty=int(row["quantity"]),
    )
    for row in items
  )


def customer_slip(order: dict, items: list[dict], lang: str) -> str:
  status = order["status"]
  lines = [
    t(lang, "slip_id", code=order_code(order["id"])),
    _product_lines(items, lang),
    t(lang, "slip_status", status=escape(_status_label(lang, status))),
    t(lang, "slip_sum", total=format_price(order["total_price"])),
  ]
  if status in READY_STATUSES:
    lines.extend(
      [
        t(lang, "slip_address", address=t(lang, "pickup_address")),
        t(lang, "slip_hours", hours=t(lang, "pickup_hours")),
        t(lang, "slip_contact", contact=PICKUP_CONTACT, phone=PICKUP_PHONE),
      ]
    )
  return "\n".join(lines)


async def _stock_lines(items: list[dict], lang: str) -> str:
  lines: list[str] = []
  for row in items:
    product = await asyncio.to_thread(get_product, int(row["product_id"]))
    left = "—" if not product else str(product.get("quantity", "—"))
    name = escape(str(row.get("product_name") or t(lang, "product_fallback")))
    lines.append(t(lang, "stock_line", name=name, qty=int(row["quantity"]), left=left))
  return "\n".join(lines) if lines else "—"


async def staff_slip(order: dict, items: list[dict], lang: str) -> str:
  name = escape(str(order.get("user_name") or "—"))
  phone = escape(str(order.get("phone_number") or "—"))
  goods = await _stock_lines(items, lang)
  return t(
    lang,
    "staff_slip",
    code=order_code(order["id"]),
    name=name,
    phone=phone,
    total=format_price(order["total_price"]),
    status=escape(_status_label(lang, order["status"])),
    goods=goods,
  )


async def notify_customer_delivered(bot, order: dict) -> None:
  user_id = order.get("user_id")
  if not user_id:
    return
  lang = await asyncio.to_thread(get_user_language, int(user_id))
  text = t(lang, "delivered_notice", code=order_code(order["id"]))
  try:
    await bot.send_message(int(user_id), text)
  except Exception:
    logger.warning("Topshirish xabari yuborilmadi user=%s", user_id)


async def confirm_delivery(
  message: Message,
  order_id: int,
  *,
  staff_id: int,
  lang: str = "uz",
) -> None:
  """Xodim tasdig'i: status paid/approved → delivered, mijozga xabar."""
  if not is_admin(staff_id):
    await message.answer(t(lang, "staff_only"))
    return

  order, items = await _order_bundle(order_id)
  if not order:
    await message.answer(t(lang, "order_not_found"))
    return
  already = order["status"] == "delivered"
  ok, result = await asyncio.to_thread(mark_order_delivered, order_id)
  if not ok:
    await message.answer(f"❌ {escape(result)}")
    return
  if already or "allaqachon" in result.lower():
    await message.answer(
      t(lang, "already_delivered", code=order_code(order_id)),
      reply_markup=role_reply_keyboard(True, lang),
    )
    return
  await notify_customer_delivered(message.bot, order)
  await message.answer(
    t(lang, "delivered_ok", code=order_code(order_id))
    + f"\n👤 {escape(str(order.get('user_name') or '—'))}\n"
    + _product_lines(items, lang),
    reply_markup=role_reply_keyboard(True, lang),
  )


async def show_my_orders(message: Message, user_id: int, lang: str = "uz") -> None:
  orders = await asyncio.to_thread(get_user_orders, user_id)
  if not orders:
    await message.answer(
      t(lang, "no_orders"),
      reply_markup=_client_kb(user_id, lang),
    )
    return

  active = [order for order in orders if order["status"] in ACTIVE_STATUSES]
  history = [order for order in orders if order["status"] not in ACTIVE_STATUSES]
  if not active:
    await message.answer(
      t(lang, "no_active"),
      reply_markup=_client_kb(user_id, lang),
    )
  for order in active:
    items = await asyncio.to_thread(get_order_items, int(order["id"]))
    ready = order["status"] in READY_STATUSES
    await message.answer(
      customer_slip(order, items, lang),
      reply_markup=order_slip_keyboard(
        int(order["id"]),
        ready=ready,
        pending=order["status"] == "pending",
        lang=lang,
      ),
    )
  if history:
    lines = [t(lang, "history_title") + "\n"]
    for order in history[:10]:
      state = _status_label(lang, order["status"])
      lines.append(
        f"{order_code(order['id'])} — {format_price(order['total_price'])}\n"
        f"   {escape(state)}"
      )
    await message.answer("\n".join(lines), reply_markup=_client_kb(user_id, lang))


async def handle_claim_start(
  message: Message,
  order_id: int,
  lang: str = "uz",
  user_id: int | None = None,
) -> None:
  """QR skaneridan /start claim_{id}."""
  actor_id = user_id if user_id is not None else (
    message.from_user.id if message.from_user else None
  )
  admin_user = is_admin(actor_id)
  order, items = await _order_bundle(order_id)
  keyboard = role_reply_keyboard(admin_user, lang)
  if not order:
    await message.answer(t(lang, "order_not_found"), reply_markup=keyboard)
    return

  if admin_user and actor_id is not None:
    await message.answer(
      await staff_slip(order, items, lang),
      reply_markup=keyboard,
    )
    if order["status"] in READY_STATUSES:
      await confirm_delivery(message, order_id, staff_id=actor_id, lang=lang)
    elif order["status"] == "delivered":
      await message.answer(t(lang, "already_delivered", code=order_code(order_id)))
    else:
      await message.answer(t(lang, "not_paid_yet"))
    return

  if actor_id is not None and int(order["user_id"]) == int(actor_id):
    await message.answer(t(lang, "your_claim_code"), reply_markup=keyboard)
    await message.answer(
      customer_slip(order, items, lang),
      reply_markup=order_slip_keyboard(
        order_id,
        ready=order["status"] in READY_STATUSES,
        pending=order["status"] == "pending",
        lang=lang,
      ),
    )
    return

  await message.answer(t(lang, "claim_staff_only"), reply_markup=keyboard)


async def _busy_ordering(message: Message, state: FSMContext, lang: str) -> bool:
  current = await state.get_state()
  if current not in {
    OrderStates.waiting_quantity.state,
    OrderStates.waiting_phone.state,
  }:
    return False
  await message.answer(
    t(lang, "ordering_busy", cancel=t(lang, "btn_cancel")),
    reply_markup=phone_request_keyboard(lang)
    if current == OrderStates.waiting_phone.state
    else cancel_reply_keyboard(lang),
  )
  return True


@router.message(F.text.in_(button_values("btn_orders")))
async def on_my_orders(message: Message, state: FSMContext, lang: str) -> None:
  if await _busy_ordering(message, state, lang):
    return
  await state.clear()
  await show_my_orders(message, message.from_user.id, lang)


@router.message(F.text.in_(button_values("btn_pickup")))
@router.callback_query(F.data == "order:pickup")
async def on_pickup_guide(
  event: Message | CallbackQuery,
  state: FSMContext,
  lang: str,
) -> None:
  guide = t(lang, "pickup_guide", contact=PICKUP_CONTACT, phone=PICKUP_PHONE)
  if isinstance(event, CallbackQuery):
    await event.answer()
    if event.message is not None:
      await event.message.answer(guide)
    return
  if await _busy_ordering(event, state, lang):
    return
  await state.clear()
  await event.answer(guide, reply_markup=_client_kb(event.from_user.id, lang))


@router.callback_query(F.data.startswith("order:qr:"))
async def on_order_qr(callback: CallbackQuery, lang: str) -> None:
  raw = (callback.data or "").rsplit(":", 1)[-1]
  if not raw.isdigit():
    await callback.answer(t(lang, "order_not_found"), show_alert=True)
    return
  order_id = int(raw)
  order, _items = await _order_bundle(order_id)
  if not order or int(order["user_id"]) != callback.from_user.id:
    await callback.answer(t(lang, "no_permission"), show_alert=True)
    return
  if order["status"] not in READY_STATUSES:
    await callback.answer(t(lang, "qr_paid_only"), show_alert=True)
    return
  await callback.answer()
  png = await asyncio.to_thread(build_claim_qr_png, order_id)
  photo = BufferedInputFile(png.getvalue(), filename=png.name)
  await callback.message.answer_photo(
    photo,
    caption=t(lang, "qr_caption", code=order_code(order_id)),
  )


@router.message(StateFilter(None), IsAdminFilter(), F.text.regexp(ORDER_CODE_RE))
async def on_staff_lookup(message: Message, lang: str) -> None:
  order_id = parse_order_code(message.text)
  if order_id is None:
    return
  order, items = await _order_bundle(order_id)
  if not order:
    await message.answer(t(lang, "order_not_found"))
    return
  markup = (
    deliver_order_keyboard(order_id)
    if order["status"] in READY_STATUSES
    else None
  )
  await message.answer(await staff_slip(order, items, lang), reply_markup=markup)


@router.callback_query(F.data.startswith("order:deliver:"))
async def on_staff_deliver(callback: CallbackQuery, lang: str) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer(t(lang, "no_permission"), show_alert=True)
    return
  raw = (callback.data or "").rsplit(":", 1)[-1]
  if not raw.isdigit() or callback.message is None:
    await callback.answer(t(lang, "order_not_found"), show_alert=True)
    return
  await callback.answer()
  await confirm_delivery(
    callback.message,
    int(raw),
    staff_id=callback.from_user.id,
    lang=lang,
  )
