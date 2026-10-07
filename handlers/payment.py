"""Telegram Payments — Click va Payme: invoice, pre-checkout, successful_payment."""

from __future__ import annotations

import asyncio
import logging
from html import escape

from aiogram import Bot, F, Router
from aiogram.types import (
  CallbackQuery,
  LabeledPrice,
  Message,
  PreCheckoutQuery,
)

from config import (
  ADMIN_IDS,
  CLICK_PROVIDER_TOKEN,
  PAYMENT_CURRENCY,
  PAYME_PROVIDER_TOKEN,
)
from filters.admin import is_admin
from keyboards import client_reply_keyboard, pay_order_keyboard
from supabase_db import (
  format_price,
  get_order,
  get_order_items,
  mark_order_paid,
  parse_payment_payload,
  som_to_tiyin,
  tiyin_to_som,
  validate_order_for_payment,
)

logger = logging.getLogger(__name__)
router = Router(name="payment")

# Telegram UZS. Click hujjatidagi pastki chegara 10 000 so'm, Payme — 1 000 so'm.
PROVIDERS: dict[str, dict[str, object]] = {
  "click": {
    "label": "Click",
    "token": CLICK_PROVIDER_TOKEN,
    "min_som": 10_000,
  },
  "payme": {
    "label": "Payme",
    "token": PAYME_PROVIDER_TOKEN,
    "min_som": 1_000,
  },
}
INVOICE_TITLE_LIMIT = 32
INVOICE_DESCRIPTION_LIMIT = 255
PRICE_LABEL_LIMIT = 32


def available_providers() -> list[tuple[str, str]]:
  return [
    (code, str(meta["label"]))
    for code, meta in PROVIDERS.items()
    if meta.get("token")
  ]


def payments_configured() -> bool:
  return bool(available_providers())


def _provider_meta(code: str) -> dict[str, object] | None:
  meta = PROVIDERS.get(code)
  if not meta or not meta.get("token"):
    return None
  return meta


def _hide_tokens(text: str) -> str:
  for meta in PROVIDERS.values():
    token = str(meta.get("token") or "")
    if token:
      text = text.replace(token, "***")
  return text


def _invoice_title(order_id: int) -> str:
  title = f"TATU Brand Shop Buyurtma #{order_id}"
  if len(title) <= INVOICE_TITLE_LIMIT:
    return title
  return f"Buyurtma #{order_id}"[:INVOICE_TITLE_LIMIT]


def _invoice_description(order_id: int, items: list[dict]) -> str:
  lines: list[str] = []
  for item in items[:8]:
    name = (item.get("product_name") or "Mahsulot").strip()
    lines.append(f"• {name} × {item['quantity']}")
  if len(items) > 8:
    lines.append(f"• … va yana {len(items) - 8} ta")
  description = "\n".join(lines) if lines else f"Buyurtma #{order_id}"
  if len(description) > INVOICE_DESCRIPTION_LIMIT:
    return description[: INVOICE_DESCRIPTION_LIMIT - 3] + "..."
  return description


def _invoice_prices(order_id: int, items: list[dict], total_som: int) -> list[LabeledPrice]:
  """Har bir qatorni tiyinga o'tkazadi. Yig'indi buyurtma summasiga teng bo'lmasa — bitta qator."""
  prices: list[LabeledPrice] = []
  summed = 0
  for item in items:
    qty = int(item["quantity"])
    unit = int(item.get("unit_price") or 0)
    if qty <= 0 or unit < 0:
      return [
        LabeledPrice(
          label=f"Buyurtma #{order_id}"[:PRICE_LABEL_LIMIT],
          amount=som_to_tiyin(total_som),
        )
      ]
    label = f"{(item.get('product_name') or 'Mahsulot').strip()} × {qty}"
    prices.append(
      LabeledPrice(
        label=label[:PRICE_LABEL_LIMIT],
        amount=som_to_tiyin(unit * qty),
      )
    )
    summed += unit * qty

  if not prices or summed != total_som:
    return [
      LabeledPrice(
        label=f"Buyurtma #{order_id}"[:PRICE_LABEL_LIMIT],
        amount=som_to_tiyin(total_som),
      )
    ]
  return prices


def _evaluate_pre_checkout(
  payload: str,
  user_id: int,
  total_amount: int,
  currency: str,
) -> tuple[bool, str]:
  """Sinxron tekshiruv — pre-checkout 10 soniya ichida javob berishi uchun bitta chaqiruv."""
  order_id, _provider = parse_payment_payload(payload)
  if order_id is None:
    return False, "Noto'g'ri to'lov ma'lumoti."

  order = get_order(order_id)
  if not order:
    return False, "Buyurtma topilmadi."
  if int(order["user_id"]) != int(user_id):
    return False, "Bu to'lov sizning buyurtmangizga tegishli emas."
  if int(total_amount) != som_to_tiyin(int(order["total_price"])):
    return False, "To'lov summasi o'zgargan. Qaytadan urinib ko'ring."
  if (currency or "").upper() != PAYMENT_CURRENCY:
    return False, "Valyuta qo'llab-quvvatlanmaydi."

  ok, message = validate_order_for_payment(order_id)
  if not ok:
    return False, message
  return True, "OK"


async def send_order_invoice(
  bot: Bot,
  chat_id: int,
  order: dict,
  *,
  provider: str,
  intro_text: str | None = None,
) -> bool:
  """Tanlangan provayder (Click yoki Payme) uchun invoys yuboradi."""
  meta = _provider_meta(provider)
  if meta is None:
    await bot.send_message(
      chat_id,
      "⚠️ Bu to'lov usuli sozlanmagan. Boshqa usulni tanlang.",
      reply_markup=pay_order_keyboard(int(order["id"])),
    )
    return False

  label = str(meta["label"])
  token = str(meta["token"])
  min_som = int(meta["min_som"])
  order_id = int(order["id"])
  ok, message = await asyncio.to_thread(validate_order_for_payment, order_id)
  if not ok:
    await bot.send_message(chat_id, f"❌ {message}")
    return False

  items = await asyncio.to_thread(get_order_items, order_id)
  total_som = int(order["total_price"])
  if total_som < min_som:
    await bot.send_message(
      chat_id,
      f"❌ {label} orqali minimal to'lov {format_price(min_som)}.\n"
      "Buyurtma saqlandi — boshqa usulni tanlang yoki savatga mahsulot qo'shing.",
      reply_markup=pay_order_keyboard(order_id),
    )
    return False

  if intro_text:
    await bot.send_message(chat_id, intro_text)

  try:
    await bot.send_invoice(
      chat_id=chat_id,
      title=_invoice_title(order_id),
      description=_invoice_description(order_id, items),
      payload=f"order_{order_id}:{provider}",
      provider_token=token,
      currency=PAYMENT_CURRENCY,
      prices=_invoice_prices(order_id, items, total_som),
      start_parameter=f"order-{order_id}-{provider}",
      need_name=True,
      need_phone_number=True,
      send_phone_number_to_provider=True,
    )
  except Exception as error:
    logger.exception("send_invoice xato order=%s provider=%s", order_id, provider)
    detail = escape(_hide_tokens(str(error)))[:300]
    await bot.send_message(
      chat_id,
      f"❌ {label} oynasi ochilmadi. Buyurtma saqlandi — "
      "quyidagi tugma orqali qayta urinib ko'ring.\n"
      f"<code>{detail}</code>",
      reply_markup=pay_order_keyboard(order_id),
    )
    return False
  return True


@router.callback_query(F.data.startswith("client:pay:"))
async def cb_pay_order(callback: CallbackQuery) -> None:
  parts = (callback.data or "").split(":")
  raw = parts[2] if len(parts) > 2 else ""
  provider = parts[3].strip().lower() if len(parts) > 3 else ""
  if not raw.isdigit():
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return

  order = await asyncio.to_thread(get_order, int(raw))
  if not order:
    await callback.answer("Buyurtma topilmadi.", show_alert=True)
    return
  if int(order["user_id"]) != callback.from_user.id and not is_admin(
    callback.from_user.id
  ):
    await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
    return

  if _provider_meta(provider) is None:
    await callback.answer()
    chat = callback.message
    text = "💳 To'lov usulini tanlang:"
    markup = pay_order_keyboard(int(order["id"]))
    if chat is not None:
      await chat.answer(text, reply_markup=markup)
    else:
      await callback.bot.send_message(callback.from_user.id, text, reply_markup=markup)
    return

  await callback.answer()
  chat_id = (
    callback.message.chat.id
    if callback.message is not None
    else callback.from_user.id
  )
  label = str(PROVIDERS[provider]["label"])
  await send_order_invoice(
    callback.bot,
    chat_id,
    order,
    provider=provider,
    intro_text=f"💳 Buyurtma #{order['id']} — {label}:",
  )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
  """Pul yechilishidan oldin ombor tekshiruvi. Javob 10 soniya ichida."""
  try:
    ok, message = await asyncio.to_thread(
      _evaluate_pre_checkout,
      query.invoice_payload or "",
      query.from_user.id,
      int(query.total_amount),
      query.currency or "",
    )
  except Exception:
    logger.exception("pre_checkout xato payload=%s", query.invoice_payload)
    await query.answer(
      ok=False,
      error_message="To'lovni vaqtincha tekshirib bo'lmadi. Qayta urinib ko'ring.",
    )
    return

  if not ok:
    await query.answer(ok=False, error_message=message[:200])
    return
  await query.answer(ok=True)


def _payer_contacts(message: Message, order: dict | None) -> tuple[str, str]:
  payment = message.successful_payment
  info = payment.order_info if payment else None
  name = (
    (info.name if info and info.name else None)
    or (order or {}).get("user_name")
    or message.from_user.full_name
    or "—"
  )
  phone = (
    (info.phone_number if info and info.phone_number else None)
    or (order or {}).get("phone_number")
    or "—"
  )
  return str(name), str(phone)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
  payment = message.successful_payment
  if not payment:
    return

  order_id, provider = parse_payment_payload(payment.invoice_payload or "")
  if order_id is None:
    await message.answer("❌ To'lov qabul qilindi, lekin buyurtma topilmadi.")
    logger.error("successful_payment unknown payload: %s", payment.invoice_payload)
    return

  label = str(PROVIDERS.get(provider, {}).get("label") or "To'lov")
  charge_id = (
    payment.provider_payment_charge_id
    or payment.telegram_payment_charge_id
    or "—"
  )
  safe_charge = escape(charge_id)
  try:
    ok, status_message = await asyncio.to_thread(
      mark_order_paid,
      order_id,
      charge_id if charge_id != "—" else None,
      provider,
    )
  except Exception as error:
    logger.exception("mark_order_paid xato order=%s", order_id)
    ok, status_message = False, str(error)

  paid_som = tiyin_to_som(int(payment.total_amount))
  order = await asyncio.to_thread(get_order, order_id)
  items = await asyncio.to_thread(get_order_items, order_id)
  payer_name, payer_phone = _payer_contacts(message, order)
  fresh_payment = ok and "allaqachon" not in status_message.lower()

  if not ok:
    logger.error(
      "To'lov o'tdi lekin baza yangilanmadi order=%s: %s",
      order_id,
      status_message,
    )
    await message.answer(
      f"⚠️ To'lov qabul qilindi, lekin buyurtma #{order_id} ni "
      f"yangilab bo'lmadi.\nSabab: {status_message}\n"
      f"🧾 {label} ID: <code>{safe_charge}</code>\n"
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
          f"👤 {payer_name}\n"
          f"📞 {payer_phone}\n"
          f"💰 {format_price(paid_som)}\n"
          f"{status_message}\n"
          f"🧾 {label}: <code>{safe_charge}</code>",
        )
      except Exception:
        logger.warning("Admin %s ga xato-notify yuborilmadi", admin_id)
    return

  item_lines = "\n".join(
    f"• {row.get('product_name') or 'Mahsulot'} × {row['quantity']}"
    for row in items
  ) or "—"

  await message.answer(
    f"✅ <b>To'lov tasdiqlandi</b>\n\n"
    f"🆔 Buyurtma: <b>#{order_id}</b>\n"
    f"💰 Summa: <b>{format_price(paid_som)}</b>\n"
    f"🧾 {label} ID: <code>{safe_charge}</code>\n\n"
    f"{item_lines}\n\n"
    "Tez orada buyurtmangiz bilan bog'lanamiz.",
    reply_markup=client_reply_keyboard(
      show_admin_back=is_admin(message.from_user.id)
    ),
  )

  if not fresh_payment:
    return

  notify = (
    f"💳 <b>To'langan buyurtma #{order_id}</b>\n"
    f"👤 {payer_name}\n"
    f"📞 {payer_phone}\n"
    f"💰 {format_price(paid_som)}\n"
    f"🧾 {label}: <code>{safe_charge}</code>\n\n"
    f"{item_lines}"
  )
  for admin_id in ADMIN_IDS:
    try:
      await message.bot.send_message(admin_id, notify)
    except Exception as error:
      logger.warning("Admin %s ga notify yuborilmadi: %s", admin_id, error)
