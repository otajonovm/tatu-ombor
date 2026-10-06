from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS, ORDER_STATUS_LABELS, SHOP_ABOUT
from supabase_db import (
  add_to_cart,
  cart_details,
  clear_cart,
  create_order,
  format_price,
  get_active_products,
  get_product,
  get_user_orders,
)
from filters.admin import is_admin
from keyboards import (
  BTN_ABOUT,
  BTN_CART,
  BTN_CATALOG,
  BTN_MY_ORDERS,
  cancel_inline_keyboard,
  cancel_reply_keyboard,
  cart_keyboard,
  catalog_keyboard,
  client_reply_keyboard,
  product_buy_keyboard,
)
from states import OrderStates
from utils.media import replace_with_text, send_product_card

router = Router(name="client")


def _client_kb(user_id: int):
  return client_reply_keyboard(show_admin_back=is_admin(user_id))


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


# ── Reply menyu ────────────────────────────────────────────


@router.message(F.text == BTN_CATALOG)
async def show_catalog(message: Message, state: FSMContext) -> None:
  await state.clear()
  products = get_active_products()
  if not products:
    await message.answer(
      "🛍 Hozircha sotuvda mahsulot yo'q.",
      reply_markup=_client_kb(message.from_user.id),
    )
    return
  await message.answer(
    "🛍 <b>Katalog</b>\n\nMavjud mahsulotni tanlang:",
    reply_markup=catalog_keyboard(products),
  )


@router.message(F.text == BTN_CART)
async def show_cart(message: Message, state: FSMContext) -> None:
  await state.clear()
  await _send_cart(message, message.from_user.id)


@router.message(F.text == BTN_MY_ORDERS)
async def show_my_orders(message: Message, state: FSMContext) -> None:
  await state.clear()
  orders = get_user_orders(message.from_user.id)
  if not orders:
    await message.answer(
      "📦 Sizda hali buyurtmalar yo'q.",
      reply_markup=_client_kb(message.from_user.id),
    )
    return

  lines = ["📦 <b>Mening buyurtmalarim</b>\n"]
  for order in orders:
    status = ORDER_STATUS_LABELS.get(order["status"], order["status"])
    created = order["created_at"]
    created_s = created.strftime("%Y-%m-%d %H:%M") if hasattr(created, "strftime") else str(created)
    lines.append(
      f"#{order['id']} — {format_price(order['total_price'])}\n"
      f"   {status}\n"
      f"   📅 {created_s}\n"
    )
  await message.answer(
    "\n".join(lines),
    reply_markup=_client_kb(message.from_user.id),
  )


@router.message(F.text == BTN_ABOUT)
async def show_about(message: Message, state: FSMContext) -> None:
  await state.clear()
  await message.answer(
    SHOP_ABOUT,
    reply_markup=_client_kb(message.from_user.id),
  )


# ── Inline: katalog / mahsulot ─────────────────────────────


@router.callback_query(F.data == "client:catalog")
async def cb_catalog(callback: CallbackQuery, state: FSMContext) -> None:
  await state.clear()
  await callback.answer()
  products = get_active_products()
  if not products:
    await replace_with_text(
      callback.message,
      "🛍 Hozircha sotuvda mahsulot yo'q.",
    )
    return
  await replace_with_text(
    callback.message,
    "🛍 <b>Katalog</b>\n\nMavjud mahsulotni tanlang:",
    catalog_keyboard(products),
  )


@router.callback_query(F.data.startswith("client:product:"))
async def cb_product(callback: CallbackQuery, state: FSMContext) -> None:
  await state.clear()
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer("Mahsulot mavjud emas.", show_alert=True)
    return
  await callback.answer()
  await send_product_card(
    callback.message,
    product,
    product_buy_keyboard(product_id),
  )


@router.callback_query(F.data.startswith("client:addcart:"))
async def cb_add_cart(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer("Mahsulot mavjud emas.", show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_quantity)
  await state.update_data(mode="cart", product_id=product_id)
  await replace_with_text(
    callback.message,
    f"🛒 <b>{product['name']}</b>\n"
    f"Qoldiq: <b>{product['quantity']}</b> dona\n\n"
    "Nechta dona qo'shiladi? Raqam kiriting:",
    cancel_inline_keyboard(),
  )


@router.callback_query(F.data.startswith("client:buynow:"))
async def cb_buy_now(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product or not product["is_active"] or product["quantity"] <= 0:
    await callback.answer("Mahsulot mavjud emas.", show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_quantity)
  await state.update_data(mode="buynow", product_id=product_id)
  await replace_with_text(
    callback.message,
    f"⚡️ <b>Tezkor buyurtma</b>\n"
    f"Mahsulot: <b>{product['name']}</b>\n"
    f"Qoldiq: <b>{product['quantity']}</b> dona\n\n"
    "Nechta dona kerak? Raqam kiriting:",
    cancel_inline_keyboard(),
  )


@router.message(OrderStates.waiting_quantity, F.text)
async def process_quantity(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip()
  if not text.isdigit() or int(text) <= 0:
    await message.answer(
      "❌ Musbat butun son kiriting:",
      reply_markup=cancel_reply_keyboard(),
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
      "Mahsulot topilmadi.",
      reply_markup=_client_kb(message.from_user.id),
    )
    return

  if quantity > product["quantity"]:
    await message.answer(
      f"❌ Omborda faqat <b>{product['quantity']}</b> dona bor.\n"
      "Kamroq miqdor kiriting:",
      reply_markup=cancel_reply_keyboard(),
    )
    return

  if mode == "cart":
    add_to_cart(message.from_user.id, product_id, quantity)
    await state.clear()
    await message.answer(
      f"✅ Savatga qo'shildi: <b>{product['name']}</b> × {quantity}",
      reply_markup=_client_kb(message.from_user.id),
    )
    await _send_cart(message, message.from_user.id)
    return

  # Tezkor buyurtma — telefon so'rash
  await state.update_data(buynow_qty=quantity)
  await state.set_state(OrderStates.waiting_phone)
  await message.answer(
    "📞 Telefon raqamingizni yuboring\n"
    "(masalan: +998901234567):",
    reply_markup=cancel_reply_keyboard(),
  )


@router.callback_query(F.data == "client:clearcart")
async def cb_clear_cart(callback: CallbackQuery) -> None:
  clear_cart(callback.from_user.id)
  await callback.answer("Savat tozalandi.")
  await replace_with_text(
    callback.message,
    "🛒 Savat bo'sh.",
    cart_keyboard(False),
  )


@router.callback_query(F.data == "client:checkout")
async def cb_checkout(callback: CallbackQuery, state: FSMContext) -> None:
  items, total = cart_details(callback.from_user.id)
  if not items:
    await callback.answer("Savat bo'sh.", show_alert=True)
    return

  await callback.answer()
  await state.set_state(OrderStates.waiting_phone)
  await state.update_data(mode="cart_checkout")
  await replace_with_text(
    callback.message,
    f"✅ Buyurtma summasi: <b>{format_price(total)}</b>\n\n"
    "📞 Telefon raqamingizni yuboring\n"
    "(masalan: +998901234567):",
    cancel_inline_keyboard(),
  )


@router.message(OrderStates.waiting_phone, F.text)
async def process_phone(message: Message, state: FSMContext) -> None:
  phone = _normalize_phone(message.text or "")
  if not phone:
    await message.answer(
      "❌ Telefon raqam noto'g'ri. Qayta yuboring:",
      reply_markup=cancel_reply_keyboard(),
    )
    return

  data = await state.get_data()
  mode = data.get("mode")
  user = message.from_user
  user_name = user.full_name or user.username or str(user.id)

  order_items: list[dict] = []

  if mode == "buynow" or data.get("buynow_qty"):
    product_id = data.get("product_id")
    qty = data.get("buynow_qty")
    product = get_product(product_id) if product_id else None
    if not product or not qty:
      await state.clear()
      await message.answer(
        "Xatolik. Qaytadan boshlang.",
        reply_markup=_client_kb(user.id),
      )
      return
    if product["quantity"] < qty:
      await state.clear()
      await message.answer(
        f"❌ Qoldiq yetarli emas ({product['quantity']} dona).",
        reply_markup=_client_kb(user.id),
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
        "🛒 Savat bo'sh.",
        reply_markup=_client_kb(user.id),
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

  order = create_order(user.id, user_name, phone, order_items)
  await state.clear()

  if not order:
    await message.answer(
      "❌ Buyurtma yaratilmadi. Qoldiqni tekshirib, qayta urinib ko'ring.",
      reply_markup=_client_kb(user.id),
    )
    return

  if mode != "buynow" and not data.get("buynow_qty"):
    clear_cart(user.id)

  await message.answer(
    f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
    f"🆔 Raqam: <b>#{order['id']}</b>\n"
    f"💰 Summa: <b>{format_price(order['total_price'])}</b>\n"
    f"📞 Tel: <b>{phone}</b>\n"
    f"⏳ Holat: <b>Kutilmoqda</b>\n\n"
    "Admin tasdiqlagach holat «Mening buyurtmalarim» da yangilanadi.",
    reply_markup=_client_kb(user.id),
  )

  notify = (
    f"🔔 <b>Yangi buyurtma #{order['id']}</b>\n"
    f"👤 {user_name}\n"
    f"📞 {phone}\n"
    f"💰 {format_price(order['total_price'])}\n\n"
    "Tasdiqlash: «📋 Yangi buyurtmalar»"
  )
  for admin_id in ADMIN_IDS:
    try:
      await message.bot.send_message(admin_id, notify)
    except Exception:
      pass


@router.callback_query(F.data == "client:cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
  await state.clear()
  await callback.answer("Bekor qilindi.")
  await replace_with_text(callback.message, "❌ Bekor qilindi.")


@router.message(OrderStates.waiting_quantity)
async def quantity_hint(message: Message) -> None:
  await message.answer(
    "🔢 Miqdorni raqam bilan yozing:",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(OrderStates.waiting_phone)
async def phone_hint(message: Message) -> None:
  await message.answer(
    "📞 Telefon raqamni matn ko'rinishida yuboring:",
    reply_markup=cancel_reply_keyboard(),
  )


async def _send_cart(message: Message, user_id: int) -> None:
  items, total = cart_details(user_id)
  if not items:
    await message.answer(
      "🛒 Savat bo'sh.",
      reply_markup=_client_kb(user_id),
    )
    await message.answer(
      "Mahsulot qo'shish uchun katalogga o'ting.",
      reply_markup=cart_keyboard(False),
    )
    return

  lines = ["🛒 <b>Savat</b>\n"]
  for row in items:
    p = row["product"]
    lines.append(
      f"• {p['name']} × {row['quantity']} = {format_price(row['line_total'])}"
    )
  lines.append(f"\n💰 Jami: <b>{format_price(total)}</b>")
  await message.answer(
    "\n".join(lines),
    reply_markup=cart_keyboard(True),
  )
