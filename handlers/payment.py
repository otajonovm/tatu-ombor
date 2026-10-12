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
from locales import t
from locales.products import localized_name
from supabase_db import (
  format_price,
  get_order,
  get_order_items,
  get_user_language,
  mark_order_paid,
  parse_payment_payload,
  som_to_tiyin,
  tiyin_to_som,
  validate_order_for_payment,
)

logger = logging.getLogger(__name__)
router = Router(name="payment")

_PAYMENT_ERRORS = {
  "Noto'g'ri to'lov ma'lumoti.": "err_bad_payload",
  "Buyurtma topilmadi.": "err_order_missing",
  "Bu to'lov sizning buyurtmangizga tegishli emas.": "err_not_owner",
  "To'lov summasi o'zgargan. Qaytadan urinib ko'ring.": "err_amount_changed",
  "Valyuta qo'llab-quvvatlanmaydi.": "err_currency",
  "Buyurtma allaqachon to'langan.": "err_already_paid",
  "Bu buyurtma uchun to'lov qabul qilinmaydi.": "err_not_payable",
  "Buyurtma summasi noto'g'ri.": "err_bad_total",
  "Buyurtmada mahsulot yo'q.": "err_no_items",
}


def user_error(lang: str, message: str) -> str:
  key = _PAYMENT_ERRORS.get(message)
  if key:
    return t(lang, key)
  prefix = "«"
  suffix = "» sotuvda emas."
  if message.startswith(prefix) and message.endswith(suffix):
    name = message[len(prefix) : -len(suffix)]
    return t(lang, "err_not_for_sale", name=escape(name))
  return message


def _client_kb(user_id: int, lang: str):
  return client_reply_keyboard(show_admin_back=is_admin(user_id), lang=lang)

# Telegram UZS. Click hujjatidagi pastki chegara 10 000 so'm, Payme — 5 000 so'm.
PROVIDERS: dict[str, dict[str, object]] = {
  "click": {
    "label": "Click",
    "token": CLICK_PROVIDER_TOKEN,
    "min_som": 10_000,
  },
  "payme": {
    "label": "Payme",
    "token": PAYME_PROVIDER_TOKEN,
    "min_som": 5_000,
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


def _plain_invoice_text(text: str) -> str:
  """Payme #, ×, • kabi belgilarni Invalid Params deb qaytarishi mumkin."""
  cleaned = "".join(ch for ch in text if ch.isalnum() or ch in " -")
  return " ".join(cleaned.split())


def _invoice_title(order_id: int) -> str:
  title = f"Buyurtma {order_id}"
  return title[:INVOICE_TITLE_LIMIT]


def _invoice_description(order_id: int, items: list[dict], lang: str = "uz") -> str:
  parts: list[str] = []
  for item in items[:8]:
    raw = localized_name(item, lang) or "Mahsulot"
    name = _plain_invoice_text(raw) or "Mahsulot"
    parts.append(f"{name} x {int(item['quantity'])}")
  if len(items) > 8:
    parts.append(f"va yana {len(items) - 8} ta")
  description = ", ".join(parts) if parts else f"Buyurtma {order_id}"
  if len(description) > INVOICE_DESCRIPTION_LIMIT:
    return description[: INVOICE_DESCRIPTION_LIMIT - 3] + "..."
  return description


def _price_label(items: list[dict], lang: str = "uz") -> str:
  """Payme ba'zi belgilarni Invalid Params deb qaytaradi, shuning uchun bitta oddiy nom."""
  raw = "Mahsulot"
  if len(items) == 1:
    raw = localized_name(items[0], lang) or "Mahsulot"
  cleaned = "".join(ch for ch in raw if ch.isalnum() or ch in " -")
  cleaned = " ".join(cleaned.split())
  return (cleaned or "Mahsulot")[:PRICE_LABEL_LIMIT]


def _invoice_prices(
  order_id: int,
  items: list[dict],
  total_som: int,
  lang: str = "uz",
) -> list[LabeledPrice]:
  """Bitta qator, summa qat'iy int tiyin: int(so'm * 100)."""
  del order_id
  amount = int(int(total_som) * 100)
  return [LabeledPrice(label=_price_label(items, lang), amount=amount)]


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
  lang: str = "uz",
) -> bool:
  """Tanlangan provayder (Click yoki Payme) uchun invoys yuboradi."""
  meta = _provider_meta(provider)
  if meta is None:
    await bot.send_message(
      chat_id,
      t(lang, "pay_provider_off"),
      reply_markup=pay_order_keyboard(int(order["id"]), lang),
    )
    return False

  label = str(meta["label"])
  token = str(meta["token"])
  min_som = int(meta["min_som"])
  order_id = int(order["id"])
  ok, message = await asyncio.to_thread(validate_order_for_payment, order_id)
  if not ok:
    await bot.send_message(chat_id, f"❌ {user_error(lang, message)}")
    return False

  items = await asyncio.to_thread(get_order_items, order_id)
  total_som = int(order["total_price"])
  if total_som < min_som:
    await bot.send_message(
      chat_id,
      t(lang, "pay_min", label=label, amount=format_price(min_som)),
      reply_markup=pay_order_keyboard(order_id, lang),
    )
    return False

  if intro_text:
    await bot.send_message(chat_id, intro_text)

  # Payme payload ichidagi ":" va telefonga yuborishni Invalid Params deb qaytaradi.
  # start_parameter faqat lotin, raqam va pastki chiziq.
  invoice_kwargs: dict[str, object] = {
    "chat_id": chat_id,
    "title": _invoice_title(order_id),
    "description": _invoice_description(order_id, items, lang),
    "payload": f"order_{order_id}_{provider}",
    "provider_token": token,
    "currency": "UZS",
    "prices": _invoice_prices(order_id, items, total_som, lang),
    "start_parameter": f"pay_order_{order_id}",
    "is_flexible": False,
  }
  if provider == "click":
    invoice_kwargs["need_name"] = True
    invoice_kwargs["need_phone_number"] = True
    invoice_kwargs["send_phone_number_to_provider"] = True

  try:
    await bot.send_invoice(**invoice_kwargs)
  except Exception as error:
    logger.exception("send_invoice xato order=%s provider=%s", order_id, provider)
    detail = escape(_hide_tokens(str(error)))[:300]
    await bot.send_message(
      chat_id,
      t(lang, "pay_window_failed", label=label, detail=detail),
      reply_markup=pay_order_keyboard(order_id, lang),
    )
    return False
  return True


@router.callback_query(F.data.startswith("client:pay:"))
async def cb_pay_order(callback: CallbackQuery, lang: str) -> None:
  parts = (callback.data or "").split(":")
  raw = parts[2] if len(parts) > 2 else ""
  provider = parts[3].strip().lower() if len(parts) > 3 else ""
  if not raw.isdigit():
    await callback.answer(t(lang, "order_not_found"), show_alert=True)
    return

  order = await asyncio.to_thread(get_order, int(raw))
  if not order:
    await callback.answer(t(lang, "order_not_found"), show_alert=True)
    return
  if int(order["user_id"]) != callback.from_user.id and not is_admin(
    callback.from_user.id
  ):
    await callback.answer(t(lang, "no_permission"), show_alert=True)
    return

  if _provider_meta(provider) is None:
    await callback.answer()
    chat = callback.message
    text = t(lang, "choose_payment")
    markup = pay_order_keyboard(int(order["id"]), lang)
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
    intro_text=t(lang, "pay_intro", order_id=order["id"], label=label),
    lang=lang,
  )


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery, lang: str) -> None:
  """Pul yechilishidan oldin ombor tekshiruvi. Javob 10 soniya ichida."""
  logger.info(
    "pre_checkout user_id=%s currency=%s total=%s payload=%s",
    query.from_user.id,
    query.currency,
    query.total_amount,
    query.invoice_payload,
  )
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
      error_message=t(lang, "pre_checkout_fail")[:200],
    )
    return

  if not ok:
    await query.answer(ok=False, error_message=user_error(lang, message)[:200])
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
async def on_successful_payment(message: Message, lang: str) -> None:
  payment = message.successful_payment
  if not payment:
    return

  order_id, provider = parse_payment_payload(payment.invoice_payload or "")
  if order_id is None:
    await message.answer(t(lang, "pay_unknown_order"))
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
      t(
        lang,
        "pay_db_fail",
        order_id=order_id,
        reason=escape(status_message),
        label=label,
        charge=safe_charge,
      ),
      reply_markup=_client_kb(message.from_user.id, lang),
    )
    for admin_id in ADMIN_IDS:
      try:
        admin_lang = await asyncio.to_thread(get_user_language, admin_id)
        await message.bot.send_message(
          admin_id,
          t(
            admin_lang,
            "admin_pay_db_fail",
            order_id=order_id,
            name=escape(payer_name),
            phone=escape(payer_phone),
            total=format_price(paid_som),
            reason=escape(status_message),
            label=label,
            charge=safe_charge,
          ),
        )
      except Exception:
        logger.warning("Admin %s ga xato-notify yuborilmadi", admin_id)
    return

  fallback = t(lang, "product_fallback")
  item_lines = "\n".join(
    f"• {escape(localized_name(row, lang) or fallback)} × {row['quantity']}"
    for row in items
  ) or "—"

  await message.answer(
    t(
      lang,
      "pay_ok",
      order_id=order_id,
      total=format_price(paid_som),
      label=label,
      charge=safe_charge,
      items=item_lines,
    ),
    reply_markup=_client_kb(message.from_user.id, lang),
  )
  from handlers.orders import show_my_orders

  await show_my_orders(message, message.from_user.id, lang)

  if not fresh_payment:
    return

  for admin_id in ADMIN_IDS:
    try:
      admin_lang = await asyncio.to_thread(get_user_language, admin_id)
      await message.bot.send_message(
        admin_id,
        t(
          admin_lang,
          "admin_paid",
          order_id=order_id,
          name=escape(payer_name),
          phone=escape(payer_phone),
          total=format_price(paid_som),
          label=label,
          charge=safe_charge,
          items=item_lines,
        ),
      )
    except Exception as error:
      logger.warning("Admin %s ga notify yuborilmadi: %s", admin_id, error)
