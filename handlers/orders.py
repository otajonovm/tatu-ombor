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

from config import (
  ORDER_STATUS_LABELS,
  PICKUP_ADDRESS,
  PICKUP_CONTACT,
  PICKUP_GUIDE,
  PICKUP_HOURS,
  PICKUP_PHONE,
)
from filters.admin import IsAdminFilter, is_admin
from keyboards import (
  BTN_MY_ORDERS,
  BTN_PICKUP,
  cancel_reply_keyboard,
  client_reply_keyboard,
  deliver_order_keyboard,
  order_slip_keyboard,
  phone_request_keyboard,
  role_reply_keyboard,
)
from states import OrderStates
from services.qr import build_claim_qr_png
from supabase_db import (
  format_price,
  get_order,
  get_order_items,
  get_product,
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


def _client_kb(user_id: int):
  return client_reply_keyboard(show_admin_back=is_admin(user_id))


async def _order_bundle(order_id: int) -> tuple[dict | None, list[dict]]:
  order = await asyncio.to_thread(get_order, order_id)
  if not order:
    return None, []
  items = await asyncio.to_thread(get_order_items, order_id)
  return order, items


def _product_lines(items: list[dict]) -> str:
  if not items:
    return "—"
  return "\n".join(
    f"🛍 <b>Mahsulot:</b> {escape(str(row.get('product_name') or 'Mahsulot'))} "
    f"({int(row['quantity'])} dona)"
    for row in items
  )


def customer_slip(order: dict, items: list[dict]) -> str:
  status = order["status"]
  state = ORDER_STATUS_LABELS.get(status, status)
  lines = [
    f"🆔 <b>Buyurtma ID:</b> <code>{order_code(order['id'])}</code>",
    _product_lines(items),
    f"🔘 <b>Holati:</b> {escape(state)}",
    f"💰 <b>Summa:</b> {format_price(order['total_price'])}",
  ]
  if status in READY_STATUSES:
    lines.extend(
      [
        f"📍 <b>Manzil:</b> {PICKUP_ADDRESS}",
        f"🕒 <b>Ish vaqti:</b> {PICKUP_HOURS}",
        f"📞 <b>Aloqa / Mas'ul:</b> {PICKUP_CONTACT} ({PICKUP_PHONE})",
      ]
    )
  return "\n".join(lines)


async def _stock_lines(items: list[dict]) -> str:
  lines: list[str] = []
  for row in items:
    product = await asyncio.to_thread(get_product, int(row["product_id"]))
    left = "—" if not product else str(product.get("quantity", "—"))
    name = escape(str(row.get("product_name") or "Mahsulot"))
    lines.append(f"• {name} × {int(row['quantity'])} (omborda {left} dona)")
  return "\n".join(lines) if lines else "—"


async def staff_slip(order: dict, items: list[dict]) -> str:
  status = ORDER_STATUS_LABELS.get(order["status"], order["status"])
  name = escape(str(order.get("user_name") or "—"))
  phone = escape(str(order.get("phone_number") or "—"))
  goods = await _stock_lines(items)
  return (
    f"🆔 <b>Buyurtma:</b> <code>{order_code(order['id'])}</code>\n"
    f"👤 <b>Xaridor:</b> {name}\n"
    f"📞 <b>Telefon:</b> {phone}\n"
    f"💰 <b>To'langan summa:</b> {format_price(order['total_price'])}\n"
    f"🔘 <b>Holat:</b> {escape(status)}\n\n"
    f"🛍 <b>Mahsulot:</b>\n{goods}"
  )


async def notify_customer_delivered(bot, order: dict) -> None:
  user_id = order.get("user_id")
  if not user_id:
    return
  text = (
    f"🎉 Buyurtmangiz ({order_code(order['id'])}) muvaffaqiyatli topshirildi! "
    "TATU Brand Shop'ni tanlaganingiz uchun rahmat 🎓"
  )
  try:
    await bot.send_message(int(user_id), text)
  except Exception:
    logger.warning("Topshirish xabari yuborilmadi user=%s", user_id)


async def confirm_delivery(message: Message, order_id: int, *, staff_id: int) -> None:
  """Xodim tasdig'i: status paid/approved → delivered, mijozga xabar."""
  if not is_admin(staff_id):
    await message.answer("⛔ Bu amal faqat 480-xona xodimi uchun.")
    return

  order, items = await _order_bundle(order_id)
  if not order:
    await message.answer("Buyurtma topilmadi.")
    return
  already = order["status"] == "delivered"
  ok, result = await asyncio.to_thread(mark_order_delivered, order_id)
  if not ok:
    await message.answer(f"❌ {escape(result)}")
    return
  if already or "allaqachon" in result.lower():
    await message.answer(
      f"ℹ️ {order_code(order_id)} allaqachon topshirilgan.",
      reply_markup=role_reply_keyboard(True),
    )
    return
  await notify_customer_delivered(message.bot, order)
  await message.answer(
    f"✅ {order_code(order_id)} topshirildi.\n"
    f"👤 {escape(str(order.get('user_name') or '—'))}\n"
    f"{_product_lines(items)}",
    reply_markup=role_reply_keyboard(True),
  )


async def show_my_orders(message: Message, user_id: int) -> None:
  orders = await asyncio.to_thread(get_user_orders, user_id)
  if not orders:
    await message.answer(
      "📦 Sizda hali buyurtmalar yo'q.",
      reply_markup=_client_kb(user_id),
    )
    return

  active = [order for order in orders if order["status"] in ACTIVE_STATUSES]
  history = [order for order in orders if order["status"] not in ACTIVE_STATUSES]
  if not active:
    await message.answer(
      "📦 Hozir olib ketiladigan buyurtma yo'q.",
      reply_markup=_client_kb(user_id),
    )
  for order in active:
    items = await asyncio.to_thread(get_order_items, int(order["id"]))
    ready = order["status"] in READY_STATUSES
    await message.answer(
      customer_slip(order, items),
      reply_markup=order_slip_keyboard(
        int(order["id"]),
        ready=ready,
        pending=order["status"] == "pending",
      ),
    )
  if history:
    lines = ["🗂 <b>Oldingi buyurtmalar</b>\n"]
    for order in history[:10]:
      state = ORDER_STATUS_LABELS.get(order["status"], order["status"])
      lines.append(
        f"{order_code(order['id'])} — {format_price(order['total_price'])}\n"
        f"   {escape(state)}"
      )
    await message.answer("\n".join(lines), reply_markup=_client_kb(user_id))


async def handle_claim_start(message: Message, order_id: int) -> None:
  """QR skaneridan /start claim_{id}."""
  user = message.from_user
  admin_user = is_admin(user.id if user else None)
  order, items = await _order_bundle(order_id)
  keyboard = role_reply_keyboard(admin_user)
  if not order:
    await message.answer("Buyurtma topilmadi.", reply_markup=keyboard)
    return

  if admin_user:
    await message.answer(
      await staff_slip(order, items),
      reply_markup=keyboard,
    )
    if order["status"] in READY_STATUSES:
      await confirm_delivery(message, order_id, staff_id=user.id)
    elif order["status"] == "delivered":
      await message.answer(f"ℹ️ {order_code(order_id)} allaqachon topshirilgan.")
    else:
      await message.answer(
        "Bu buyurtma hali to'lanmagan. Topshirishdan oldin to'lovni tekshiring."
      )
    return

  if user and int(order["user_id"]) == int(user.id):
    await message.answer(
      "Bu sizning olib ketish kodingiz. Uni 480-xona xodimiga ko'rsating.",
      reply_markup=keyboard,
    )
    await message.answer(
      customer_slip(order, items),
      reply_markup=order_slip_keyboard(
        order_id,
        ready=order["status"] in READY_STATUSES,
        pending=order["status"] == "pending",
      ),
    )
    return

  await message.answer(
    "Bu kod faqat 480-xona xodimi uchun.",
    reply_markup=keyboard,
  )


async def _busy_ordering(message: Message, state: FSMContext) -> bool:
  current = await state.get_state()
  if current not in {
    OrderStates.waiting_quantity.state,
    OrderStates.waiting_phone.state,
  }:
    return False
  await message.answer(
    "⏳ Buyurtma jarayoni davom etmoqda.\n"
    "Telefon yoki miqdorni yuboring, yoki «❌ Bekor qilish» ni bosing.",
    reply_markup=phone_request_keyboard()
    if current == OrderStates.waiting_phone.state
    else cancel_reply_keyboard(),
  )
  return True


@router.message(F.text == BTN_MY_ORDERS)
async def on_my_orders(message: Message, state: FSMContext) -> None:
  if await _busy_ordering(message, state):
    return
  await state.clear()
  await show_my_orders(message, message.from_user.id)


@router.message(F.text == BTN_PICKUP)
@router.callback_query(F.data == "order:pickup")
async def on_pickup_guide(event: Message | CallbackQuery, state: FSMContext) -> None:
  if isinstance(event, CallbackQuery):
    await event.answer()
    if event.message is not None:
      await event.message.answer(PICKUP_GUIDE)
    return
  if await _busy_ordering(event, state):
    return
  await state.clear()
  await event.answer(PICKUP_GUIDE, reply_markup=_client_kb(event.from_user.id))


@router.callback_query(F.data.startswith("order:qr:"))
async def on_order_qr(callback: CallbackQuery) -> None:
  raw = (callback.data or "").rsplit(":", 1)[-1]
  if not raw.isdigit():
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return
  order_id = int(raw)
  order, _items = await _order_bundle(order_id)
  if not order or int(order["user_id"]) != callback.from_user.id:
    await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
    return
  if order["status"] not in READY_STATUSES:
    await callback.answer("QR faqat to'langan buyurtma uchun.", show_alert=True)
    return
  await callback.answer()
  png = await asyncio.to_thread(build_claim_qr_png, order_id)
  photo = BufferedInputFile(png.getvalue(), filename=png.name)
  await callback.message.answer_photo(
    photo,
    caption=(
      f"🏷 <b>Olib ketish kodi</b> {order_code(order_id)}\n"
      "480-xona xodimi shu QR ni skaner qiladi."
    ),
  )


@router.message(StateFilter(None), IsAdminFilter(), F.text.regexp(ORDER_CODE_RE))
async def on_staff_lookup(message: Message) -> None:
  order_id = parse_order_code(message.text)
  if order_id is None:
    return
  order, items = await _order_bundle(order_id)
  if not order:
    await message.answer("Buyurtma topilmadi.")
    return
  markup = (
    deliver_order_keyboard(order_id)
    if order["status"] in READY_STATUSES
    else None
  )
  await message.answer(await staff_slip(order, items), reply_markup=markup)


@router.callback_query(F.data.startswith("order:deliver:"))
async def on_staff_deliver(callback: CallbackQuery) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
    return
  raw = (callback.data or "").rsplit(":", 1)[-1]
  if not raw.isdigit() or callback.message is None:
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return
  await callback.answer()
  await confirm_delivery(
    callback.message,
    int(raw),
    staff_id=callback.from_user.id,
  )
