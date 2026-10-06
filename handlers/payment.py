"""Telegram Payments (Click) — invoice, pre-checkout, successful_payment."""

from __future__ import annotations

import logging

from aiogram import Bot, F, Router
from aiogram.types import (
  CallbackQuery,
  LabeledPrice,
  Message,
  PreCheckoutQuery,
)

from config import (
  ADMIN_IDS,
  PAYMENT_CURRENCY,
  PAYMENTS_PROVIDER_TOKEN,
  SHOP_NAME,
)
from keyboards import client_reply_keyboard
from filters.admin import is_admin
from supabase_db import (
  format_price,
  get_order,
  get_order_items,
  mark_order_paid,
  parse_order_payload,
  som_to_tiyin,
  tiyin_to_som,
  validate_order_for_payment,
)

logger = logging.getLogger(__name__)
router = Router(name="payment")


def payments_configured() -> bool:
  return bool(PAYMENTS_PROVIDER_TOKEN)


async def send_order_invoice(
  bot: Bot,
  chat_id: int,
  order: dict,
  *,
  intro_text: str | None = None,
) -> bool:
  """Buyurtma uchun Click/Telegram invoysini yuboradi."""
  if not payments_configured():
    await bot.send_message(
      chat_id,
      "⚠️ To'lov tizimi sozlanmagan (PAYMENTS_PROVIDER_TOKEN).",
    )
    return False

  order_id = int(order["id"])
  ok, message = validate_order_for_payment(order_id)
  if not ok:
    await bot.send_message(chat_id, f"❌ {message}")
    return False

  items = get_order_items(order_id)
  lines = []
  for item in items[:8]:
    name = item.get("product_name") or "Mahsulot"
    lines.append(f"• {name} × {item['quantity']}")
  if len(items) > 8:
    lines.append(f"• … va yana {len(items) - 8} ta")

  total_som = int(order["total_price"])
  amount_tiyin = som_to_tiyin(total_som)
  # Telegram UZS min_amount ≈ 10 000 so'm (1_000_000 tiyin)
  if amount_tiyin < 1_000_000:
    await bot.send_message(
      chat_id,
      "❌ Click orqali minimal to'lov 10 000 so'm.\n"
      "Buyurtma saqlandi — admin bilan bog'laning yoki savatga qo'shimcha mahsulot qo'shing.",
    )
    return False

  description = "\n".join(lines) if lines else f"Buyurtma #{order_id}"
  if len(description) > 255:
    description = description[:252] + "..."

  if intro_text:
    await bot.send_message(chat_id, intro_text)

  try:
    await bot.send_invoice(
      chat_id=chat_id,
      title=f"{SHOP_NAME} #{order_id}"[:32],
      description=description,
      payload=f"order_{order_id}",
      provider_token=PAYMENTS_PROVIDER_TOKEN,
      currency=PAYMENT_CURRENCY,
      prices=[
        LabeledPrice(
          label=f"Buyurtma #{order_id}",
          amount=amount_tiyin,
        )
      ],
      start_parameter=f"order{order_id}",
    )
  except Exception as error:
    logger.exception("send_invoice xato order=%s: %s", order_id, error)
    await bot.send_message(
      chat_id,
      f"❌ Invoys ochilmadi: {error}\n"
      "Buyurtma saqlandi — quyidagi tugma orqali qayta urinib ko'ring.",
    )
    return False
  return True


@router.callback_query(F.data.startswith("client:pay:"))
async def cb_pay_order(callback: CallbackQuery) -> None:
  raw = (callback.data or "").split(":")[-1]
  if not raw.isdigit():
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return

  order = get_order(int(raw))
  if not order:
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return
  if order["user_id"] != callback.from_user.id and not is_admin(
    callback.from_user.id
  ):
    await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
    return

  await callback.answer()
  await send_order_invoice(
    callback.bot,
    callback.message.chat.id,
    order,
    intro_text=f"💳 Buyurtma #{order['id']} uchun to'lov:",
  )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
  """Telegram to'lovdan oldin — 10 soniya ichida javob berish shart."""
  order_id = parse_order_payload(query.invoice_payload or "")
  if order_id is None:
    await query.answer(ok=False, error_message="Noto'g'ri to'lov ma'lumoti.")
    return

  order = get_order(order_id)
  if not order:
    await query.answer(ok=False, error_message="Buyurtma topilmadi.")
    return

  if order["user_id"] != query.from_user.id:
    await query.answer(
      ok=False,
      error_message="Bu to'lov sizning buyurtmangizga tegishli emas.",
    )
    return

  expected_tiyin = som_to_tiyin(int(order["total_price"]))
  if int(query.total_amount) != expected_tiyin:
    await query.answer(
      ok=False,
      error_message="To'lov summasi o'zgargan. Qaytadan urinib ko'ring.",
    )
    return

  if (query.currency or "").upper() != PAYMENT_CURRENCY:
    await query.answer(ok=False, error_message="Valyuta qo'llab-quvvatlanmaydi.")
    return

  ok, message = validate_order_for_payment(order_id)
  if not ok:
    await query.answer(ok=False, error_message=message[:200])
    return

  await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
  payment = message.successful_payment
  if not payment:
    return

  order_id = parse_order_payload(payment.invoice_payload or "")
  if order_id is None:
    await message.answer("❌ To'lov qabul qilindi, lekin buyurtma topilmadi.")
    logger.error("successful_payment unknown payload: %s", payment.invoice_payload)
    return

  charge_id = (
    payment.provider_payment_charge_id
    or payment.telegram_payment_charge_id
  )
  ok, status_message = mark_order_paid(order_id, charge_id)
  paid_som = tiyin_to_som(int(payment.total_amount))
  order = get_order(order_id)
  items = get_order_items(order_id)

  if not ok:
    logger.error(
      "To'lov o'tdi lekin baza yangilanmadi order=%s: %s",
      order_id,
      status_message,
    )
    await message.answer(
      f"⚠️ To'lov qabul qilindi, lekin buyurtma #{order_id} ni "
      f"yangilab bo'lmadi.\nSabab: {status_message}\n"
      f"Click ID: <code>{charge_id}</code>\n"
      "Iltimos, admin bilan bog'laning.",
      reply_markup=client_reply_keyboard(
        show_admin_back=is_admin(message.from_user.id)
      ),
    )
    for admin_id in ADMIN_IDS:
      try:
        await message.bot.send_message(
          admin_id,
          f"🚨 To'lov o'tdi, baza xato!\n"
          f"Buyurtma #{order_id}\n"
          f"{status_message}\n"
          f"Click: <code>{charge_id}</code>",
        )
      except Exception:
        pass
    return

  item_lines = "\n".join(
    f"• {row.get('product_name') or 'Mahsulot'} × {row['quantity']}"
    for row in items
  ) or "—"

  await message.answer(
    f"✅ <b>To'lov muvaffaqiyatli!</b>\n\n"
    f"🆔 Buyurtma: <b>#{order_id}</b>\n"
    f"💰 Summa: <b>{format_price(paid_som)}</b>\n"
    f"🧾 Click ID: <code>{charge_id}</code>\n\n"
    f"{item_lines}\n\n"
    "Tez orada buyurtmangiz bilan bog'lanamiz.",
    reply_markup=client_reply_keyboard(
      show_admin_back=is_admin(message.from_user.id)
    ),
  )

  phone = (order or {}).get("phone_number", "—")
  user_name = (order or {}).get("user_name") or message.from_user.full_name
  notify = (
    f"💳 <b>To'langan buyurtma #{order_id}</b>\n"
    f"👤 {user_name}\n"
    f"📞 {phone}\n"
    f"💰 {format_price(paid_som)}\n"
    f"🧾 Click: <code>{charge_id}</code>\n\n"
    f"{item_lines}"
  )
  for admin_id in ADMIN_IDS:
    try:
      await message.bot.send_message(admin_id, notify)
    except Exception as error:
      logger.warning("Admin %s ga notify yuborilmadi: %s", admin_id, error)
