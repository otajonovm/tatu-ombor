import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import ORDER_STATUS_LABELS, TX_TYPE_LABELS
from supabase_db import (
  add_product,
  approve_order,
  delete_product,
  format_price,
  get_all_products,
  get_order,
  get_order_items,
  get_product,
  get_product_by_name,
  get_stats,
  reject_order,
  set_product_active,
  stock_in,
  update_product,
  update_product_price,
)
from filters.admin import IsAdminFilter
from keyboards import (
  BTN_ADD_PRODUCT,
  BTN_MANAGE,
  BTN_NEW_ORDERS,
  BTN_STATS,
  BTN_STOCK_IN,
  admin_manage_item_keyboard,
  admin_order_actions_keyboard,
  admin_orders_keyboard,
  admin_products_keyboard,
  admin_qr_keyboard,
  admin_reply_keyboard,
  cancel_reply_keyboard,
)
from services.qr import build_product_qr_png, product_deep_link
from states import AdminEditStates, AdminProductStates, AdminStockStates
from utils.files import IMAGES_DIR, save_telegram_photo
from utils.media import replace_with_text, send_product_card
from utils.middleware import AdminSecurityMiddleware

logger = logging.getLogger(__name__)

router = Router(name="admin")
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())
router.message.middleware(AdminSecurityMiddleware())
router.callback_query.middleware(AdminSecurityMiddleware())


# ── Mahsulot qo'shish ──────────────────────────────────────


@router.message(F.text == BTN_ADD_PRODUCT)
async def start_add_product(message: Message, state: FSMContext) -> None:
  await state.clear()
  await state.set_state(AdminProductStates.waiting_name)
  await message.answer(
    "➕ <b>Yangi mahsulot — 1/5</b>\n\nMahsulot nomini kiriting:",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminProductStates.waiting_name, F.text)
async def add_name(message: Message, state: FSMContext) -> None:
  name = (message.text or "").strip()
  if len(name) < 2 or name.isdigit():
    await message.answer("❌ Noto'g'ri nom. Qayta kiriting:")
    return
  if get_product_by_name(name):
    await message.answer("❌ Bu nom band. Boshqa nom yozing:")
    return
  await state.update_data(name=name)
  await state.set_state(AdminProductStates.waiting_description)
  await message.answer(
    "➕ <b>2/5</b> — Qisqa tavsif yozing\n"
    "(yoki «-» deb o'tkazib yuboring):",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminProductStates.waiting_description, F.text)
async def add_description(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip()
  description = "" if text == "-" else text
  await state.update_data(description=description)
  await state.set_state(AdminProductStates.waiting_price)
  await message.answer(
    "➕ <b>3/5</b> — Narxni so'mda kiriting (faqat raqam):",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminProductStates.waiting_price, F.text)
async def add_price(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip().replace(" ", "")
  if not text.isdigit() or int(text) < 0:
    await message.answer("❌ Narx noto'g'ri. Qayta kiriting:")
    return
  await state.update_data(price=int(text))
  await state.set_state(AdminProductStates.waiting_quantity)
  await message.answer(
    "➕ <b>4/5</b> — Boshlang'ich qoldiq (0 yoki undan katta):",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminProductStates.waiting_quantity, F.text)
async def add_quantity(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip()
  if not text.isdigit() or int(text) < 0:
    await message.answer("❌ Miqdor noto'g'ri. Qayta kiriting:")
    return
  await state.update_data(quantity=int(text))
  await state.set_state(AdminProductStates.waiting_image)
  await message.answer(
    "➕ <b>5/5</b> — Mahsulot rasmini foto sifatida yuboring:",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminProductStates.waiting_image, F.photo)
async def add_image(message: Message, state: FSMContext) -> None:
  data = await state.get_data()
  name = data.get("name")
  if not name:
    await state.clear()
    await message.answer("Xatolik. Qaytadan boshlang.", reply_markup=admin_reply_keyboard())
    return

  if get_product_by_name(name):
    await state.clear()
    await message.answer("❌ Bu mahsulot allaqachon mavjud.", reply_markup=admin_reply_keyboard())
    return

  photo = message.photo[-1]
  try:
    image_url = await save_telegram_photo(message.bot, photo.file_id, name)
  except Exception as error:
    logger.exception("Rasm yuklab olinmadi: %s", error)
    await message.answer("❌ Rasm saqlanmadi. Qayta yuboring:")
    return

  try:
    product = add_product(
      name=name,
      description=data.get("description", ""),
      price=int(data.get("price", 0)),
      quantity=int(data.get("quantity", 0)),
      image_url=image_url,
      image_urls=[image_url],
      admin_id=message.from_user.id,
    )
  except Exception as error:
    logger.exception("Mahsulot qo'shilmadi: %s", error)
    await message.answer(
      "❌ Mahsulot bazaga yozilmadi. Qayta urinib ko'ring yoki "
      "supabase/apply_updates.sql ni SQL Editor'da ishga tushiring."
    )
    return

  await state.clear()
  await message.answer_photo(
    photo=photo.file_id,
    caption=(
      f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
      f"🛍 {product['name']}\n"
      f"💰 {format_price(product['price'])}\n"
      f"📦 {product['quantity']} dona"
    ),
    reply_markup=admin_qr_keyboard(int(product["id"])),
  )
  await message.answer(
    "Admin menyu.",
    reply_markup=admin_reply_keyboard(),
  )


@router.callback_query(F.data.startswith("admin:qr:"))
async def generate_product_qr(callback: CallbackQuery) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Mahsulot topilmadi.", show_alert=True)
    return

  await callback.answer("QR tayyorlanmoqda...")
  try:
    me = await callback.bot.get_me()
    username = me.username or None
    png = build_product_qr_png(product_id, username)
    link = product_deep_link(product_id, username)
    caption = (
      f"📦 Mahsulot: <b>{product['name']}</b>\n"
      f"Narxi: {format_price(product['price'])}\n"
      f"🔗 <code>{link}</code>\n\n"
      "Ushbu QR kodni chop etib tovar ustiga yopishtirishingiz mumkin."
    )
    await callback.message.answer_photo(
      photo=BufferedInputFile(png.getvalue(), filename=png.name),
      caption=caption,
    )
  except Exception as error:
    logger.exception("QR yaratilmadi: %s", error)
    await callback.message.answer(f"❌ QR kod yaratilmadi: {error}")


@router.message(AdminProductStates.waiting_image)
async def add_image_invalid(message: Message) -> None:
  await message.answer("❌ Iltimos, rasmni <b>foto</b> sifatida yuboring.")


# ── Kirim ──────────────────────────────────────────────────


@router.message(F.text == BTN_STOCK_IN)
async def start_stock_in(message: Message, state: FSMContext) -> None:
  await state.clear()
  products = get_all_products(include_inactive=True)
  if not products:
    await message.answer("Mahsulotlar yo'q.", reply_markup=admin_reply_keyboard())
    return
  await message.answer(
    "📥 <b>Kirim</b> — mahsulotni tanlang:",
    reply_markup=admin_products_keyboard("stockpick"),
  )


@router.callback_query(F.data.startswith("admin:stockpick:"))
async def stock_pick(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await state.set_state(AdminStockStates.waiting_quantity)
  await state.update_data(product_id=product_id)
  await replace_with_text(
    callback.message,
    f"📥 <b>{product['name']}</b>\n"
    f"Joriy qoldiq: <b>{product['quantity']}</b>\n\n"
    "Nechta dona kirim qilinadi?",
  )


@router.message(AdminStockStates.waiting_quantity, F.text)
async def stock_quantity(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip()
  if not text.isdigit() or int(text) <= 0:
    await message.answer("❌ Musbat son kiriting:")
    return
  await state.update_data(quantity=int(text))
  await state.set_state(AdminStockStates.waiting_comment)
  await message.answer(
    "💬 Izoh yozing (ixtiyoriy) yoki «-» deb o'tkazing:",
    reply_markup=cancel_reply_keyboard(),
  )


@router.message(AdminStockStates.waiting_comment, F.text)
async def stock_comment(message: Message, state: FSMContext) -> None:
  data = await state.get_data()
  product_id = data.get("product_id")
  quantity = data.get("quantity")
  comment = (message.text or "").strip()
  if comment == "-":
    comment = None

  previous = get_product(product_id) if product_id else None
  try:
    result = stock_in(product_id, quantity, message.from_user.id, comment)
  except Exception as error:
    logger.exception("Kirim xato: %s", error)
    result = None
  await state.clear()
  if not result:
    await message.answer(
      "❌ Kirim amalga oshmadi. Qayta urinib ko'ring.",
      reply_markup=admin_reply_keyboard(),
    )
    return

  restored = ""
  if previous and not previous.get("is_active") and result.get("is_active"):
    restored = "\n♻️ Mahsulot katalogga qaytarildi."
  await message.answer(
    f"✅ Kirim qilindi!\n\n"
    f"🛍 <b>{result['name']}</b>\n"
    f"➕ +{quantity} dona\n"
    f"📦 Yangi qoldiq: <b>{result['quantity']}</b>"
    f"{restored}",
    reply_markup=admin_reply_keyboard(),
  )


# ── Mahsulotlarni boshqarish ───────────────────────────────


@router.message(F.text == BTN_MANAGE)
async def manage_list(message: Message, state: FSMContext) -> None:
  await state.clear()
  await message.answer(
    "✏️ <b>Mahsulotlarni boshqarish</b>\nTanlang:",
    reply_markup=admin_products_keyboard("managepick"),
  )


@router.callback_query(F.data == "admin:manage")
async def cb_manage(callback: CallbackQuery, state: FSMContext) -> None:
  await state.clear()
  await callback.answer()
  await replace_with_text(
    callback.message,
    "✏️ <b>Mahsulotlarni boshqarish</b>\nTanlang:",
    admin_products_keyboard("managepick"),
  )


@router.callback_query(F.data.startswith("admin:managepick:"))
async def manage_pick(callback: CallbackQuery) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await send_product_card(
    callback.message,
    product,
    admin_manage_item_keyboard(product_id, product["is_active"]),
    for_client=False,
  )


@router.callback_query(F.data.startswith("admin:editname:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await state.set_state(AdminEditStates.waiting_name)
  await state.update_data(product_id=product_id)
  await replace_with_text(
    callback.message,
    f"✏️ <b>{product['name']}</b>\n\nYangi nomni kiriting:",
  )


@router.message(AdminEditStates.waiting_name, F.text)
async def edit_name_save(message: Message, state: FSMContext) -> None:
  name = (message.text or "").strip()
  if len(name) < 2 or name.isdigit():
    await message.answer("❌ Noto'g'ri nom. Qayta kiriting:")
    return
  data = await state.get_data()
  product_id = data.get("product_id")
  existing = get_product_by_name(name)
  if existing and int(existing["id"]) != int(product_id):
    await message.answer("❌ Bu nom band. Boshqa nom yozing:")
    return
  product = update_product(product_id, {"name": name})
  await state.clear()
  if not product:
    await message.answer("Xatolik.", reply_markup=admin_reply_keyboard())
    return
  await message.answer(
    f"✅ Nom yangilandi: <b>{product['name']}</b>",
    reply_markup=admin_reply_keyboard(),
  )


@router.callback_query(F.data.startswith("admin:editprice:"))
async def edit_price_start(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await state.set_state(AdminEditStates.waiting_price)
  await state.update_data(product_id=product_id)
  await replace_with_text(
    callback.message,
    f"💰 <b>{product['name']}</b>\n"
    f"Joriy narx: {format_price(product['price'])}\n\n"
    "Yangi narxni kiriting:",
  )


@router.message(AdminEditStates.waiting_price, F.text)
async def edit_price_save(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip().replace(" ", "")
  if not text.isdigit() or int(text) < 0:
    await message.answer("❌ Narx noto'g'ri:")
    return
  data = await state.get_data()
  product = update_product_price(data["product_id"], int(text))
  await state.clear()
  if not product:
    await message.answer("Xatolik.", reply_markup=admin_reply_keyboard())
    return
  await message.answer(
    f"✅ Narx yangilandi: <b>{product['name']}</b> — {format_price(product['price'])}",
    reply_markup=admin_reply_keyboard(),
  )


@router.callback_query(F.data.startswith("admin:editqty:"))
async def edit_qty_start(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await state.set_state(AdminEditStates.waiting_quantity)
  await state.update_data(product_id=product_id)
  await replace_with_text(
    callback.message,
    f"📦 <b>{product['name']}</b>\n"
    f"Joriy miqdor: <b>{product['quantity']}</b> dona\n\n"
    "Yangi miqdorni kiriting (0 yoki undan katta):",
  )


@router.message(AdminEditStates.waiting_quantity, F.text)
async def edit_qty_save(message: Message, state: FSMContext) -> None:
  text = (message.text or "").strip()
  if not text.isdigit() or int(text) < 0:
    await message.answer("❌ Miqdor noto'g'ri. Qayta kiriting:")
    return
  data = await state.get_data()
  previous = get_product(data["product_id"])
  product = update_product(data["product_id"], {"quantity": int(text)})
  await state.clear()
  if not product:
    await message.answer("Xatolik.", reply_markup=admin_reply_keyboard())
    return
  extra = ""
  if int(product.get("quantity") or 0) <= 0:
    extra = "\n🗄 Qoldiq tugadi — mahsulot arxivlandi va katalogdan olib tashlandi."
  elif previous and not previous.get("is_active") and product.get("is_active"):
    extra = "\n♻️ Mahsulot katalogga qaytarildi."
  await message.answer(
    f"✅ Miqdor yangilandi: <b>{product['name']}</b> — {product['quantity']} dona"
    f"{extra}",
    reply_markup=admin_reply_keyboard(),
  )


@router.callback_query(F.data.startswith("admin:editimage:"))
async def edit_image_start(callback: CallbackQuery, state: FSMContext) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  await state.set_state(AdminEditStates.waiting_image)
  await state.update_data(product_id=product_id)
  await replace_with_text(
    callback.message,
    f"🖼 <b>{product['name']}</b>\n\n"
    "Yangi rasmni <b>foto</b> sifatida yuboring:",
  )


@router.message(AdminEditStates.waiting_image, F.photo)
async def edit_image_save(message: Message, state: FSMContext) -> None:
  data = await state.get_data()
  product_id = data.get("product_id")
  product = get_product(product_id) if product_id else None
  if not product:
    await state.clear()
    await message.answer("Xatolik.", reply_markup=admin_reply_keyboard())
    return

  photo = message.photo[-1]
  try:
    image_url = await save_telegram_photo(
      message.bot, photo.file_id, product["name"]
    )
  except Exception as error:
    logger.exception("Rasm yuklab olinmadi: %s", error)
    await message.answer("❌ Rasm saqlanmadi. Qayta yuboring:")
    return

  old_image = product.get("image_url")
  try:
    updated = update_product(
      product_id,
      {"image_url": image_url, "image_urls": [image_url]},
    )
  except Exception as error:
    logger.exception("Rasm bazaga yozilmadi: %s", error)
    await state.clear()
    await message.answer(
      "❌ Rasm bazaga yozilmadi. Qayta urinib ko'ring.",
      reply_markup=admin_reply_keyboard(),
    )
    return

  if not updated:
    await state.clear()
    await message.answer("Xatolik.", reply_markup=admin_reply_keyboard())
    return

  if (
    old_image
    and not str(old_image).startswith(("http://", "https://", "tgfile:"))
    and old_image != image_url
  ):
    old_path = IMAGES_DIR / old_image
    if old_path.is_file():
      try:
        old_path.unlink()
      except OSError:
        logger.warning("Eski rasm o'chirilmadi: %s", old_path)

  await state.clear()
  await message.answer_photo(
    photo=photo.file_id,
    caption=f"✅ Rasm yangilandi: <b>{updated['name']}</b>",
    reply_markup=admin_reply_keyboard(),
  )


@router.message(AdminEditStates.waiting_image)
async def edit_image_invalid(message: Message) -> None:
  await message.answer("❌ Iltimos, yangi rasmni <b>foto</b> sifatida yuboring.")


@router.callback_query(F.data.startswith("admin:toggle:"))
async def toggle_active(callback: CallbackQuery) -> None:
  product_id = int(callback.data.split(":")[2])
  product = get_product(product_id)
  if not product:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  new_state = not product["is_active"]
  set_product_active(product_id, new_state)
  await callback.answer("Faollashtirildi!" if new_state else "Arxivlandi!")
  product = get_product(product_id)
  await send_product_card(
    callback.message,
    product,
    admin_manage_item_keyboard(product_id, product["is_active"]),
    for_client=False,
  )


@router.callback_query(F.data.startswith("admin:delete:"))
async def delete_prod(callback: CallbackQuery) -> None:
  product_id = int(callback.data.split(":")[2])
  if delete_product(product_id):
    await callback.answer("O'chirildi!", show_alert=True)
  elif get_product(product_id) and set_product_active(product_id, False):
    await callback.answer(
      "Mahsulot buyurtmalarga bog'langan. Katalogdan arxivlandi.",
      show_alert=True,
    )
  else:
    await callback.answer("Mahsulot topilmadi yoki o'chirib bo'lmadi.", show_alert=True)
  await replace_with_text(
    callback.message,
    "✏️ <b>Mahsulotlarni boshqarish</b>\nTanlang:",
    admin_products_keyboard("managepick"),
  )


# ── Buyurtmalar ────────────────────────────────────────────


@router.message(F.text == BTN_NEW_ORDERS)
async def list_new_orders(message: Message, state: FSMContext) -> None:
  await state.clear()
  await message.answer(
    "📋 <b>Yangi buyurtmalar</b>\nTanlang:",
    reply_markup=admin_orders_keyboard(),
  )


@router.callback_query(F.data == "admin:orders")
async def cb_orders(callback: CallbackQuery) -> None:
  await callback.answer()
  await replace_with_text(
    callback.message,
    "📋 <b>Yangi buyurtmalar</b>\nTanlang:",
    admin_orders_keyboard(),
  )


def _format_order(order: dict, items: list[dict]) -> str:
  status = ORDER_STATUS_LABELS.get(order["status"], order["status"])
  created = order["created_at"]
  created_s = created.strftime("%Y-%m-%d %H:%M") if hasattr(created, "strftime") else str(created)
  lines = [
    f"📋 <b>Buyurtma #{order['id']}</b>",
    f"👤 {order.get('user_name') or order['user_id']}",
    f"📞 {order['phone_number']}",
    f"💰 {format_price(order['total_price'])}",
    f"🔖 {status}",
    f"📅 {created_s}",
    "",
    "<b>Tarkibi:</b>",
  ]
  for item in items:
    lines.append(
      f"• {item['product_name']} × {item['quantity']} "
      f"({format_price(item['unit_price'])})"
    )
  return "\n".join(lines)


@router.callback_query(F.data.startswith("admin:order:"))
async def order_detail(callback: CallbackQuery) -> None:
  order_id = int(callback.data.split(":")[2])
  order = get_order(order_id)
  if not order:
    await callback.answer("Topilmadi.", show_alert=True)
    return
  await callback.answer()
  items = get_order_items(order_id)
  markup = (
    admin_order_actions_keyboard(order_id)
    if order["status"] == "pending"
    else admin_orders_keyboard()
  )
  await replace_with_text(callback.message, _format_order(order, items), markup)


@router.callback_query(F.data.startswith("admin:approve:"))
async def order_approve(callback: CallbackQuery) -> None:
  order_id = int(callback.data.split(":")[2])
  ok, msg = approve_order(order_id, callback.from_user.id)
  await callback.answer(msg, show_alert=True)
  order = get_order(order_id)
  items = get_order_items(order_id) if order else []
  if order:
    await replace_with_text(
      callback.message,
      _format_order(order, items),
      admin_orders_keyboard(),
    )


@router.callback_query(F.data.startswith("admin:reject:"))
async def order_reject(callback: CallbackQuery) -> None:
  order_id = int(callback.data.split(":")[2])
  ok, msg = reject_order(order_id)
  await callback.answer(msg, show_alert=True)
  order = get_order(order_id)
  items = get_order_items(order_id) if order else []
  if order:
    await replace_with_text(
      callback.message,
      _format_order(order, items),
      admin_orders_keyboard(),
    )


# ── Statistika ─────────────────────────────────────────────


@router.message(F.text == BTN_STATS)
async def show_stats(message: Message, state: FSMContext) -> None:
  await state.clear()
  stats = get_stats()
  lines = [
    "📊 <b>Statistika</b>\n",
    f"🛍 Faol mahsulotlar: <b>{stats['active_products']}</b>",
    f"📦 Umumiy qoldiq: <b>{stats['total_stock']}</b> dona",
    f"💎 Ombordagi qiymat: <b>{format_price(stats['stock_value'])}</b>",
    "",
    f"⏳ Kutilayotgan: <b>{stats['pending_orders']}</b>",
    f"💳 To'langan: <b>{stats.get('paid_orders', 0)}</b>",
    f"✅ Qabul qilingan: <b>{stats['approved_orders']}</b>",
    f"❌ Rad etilgan: <b>{stats['rejected_orders']}</b>",
    f"🛒 Sotilgan dona: <b>{stats['sold_units']}</b>",
    f"💵 Tushum: <b>{format_price(stats['revenue'])}</b>",
    "",
    "<b>So'nggi harakatlar:</b>",
  ]
  recent = stats.get("recent") or []
  if not recent:
    lines.append("Hozircha yo'q.")
  else:
    for tx in recent:
      label = TX_TYPE_LABELS.get(tx["type"], tx["type"])
      created = tx["created_at"]
      created_s = (
        created.strftime("%m-%d %H:%M")
        if hasattr(created, "strftime")
        else str(created)
      )
      lines.append(
        f"{label} {tx['product_name']} × {tx['quantity']} ({created_s})"
      )

  await message.answer("\n".join(lines), reply_markup=admin_reply_keyboard())


# ── FSM hintlar ────────────────────────────────────────────


@router.message(AdminProductStates.waiting_name)
async def hint_name(message: Message) -> None:
  await message.answer("📝 Mahsulot nomini matn bilan yozing.")


@router.message(AdminProductStates.waiting_description)
async def hint_desc(message: Message) -> None:
  await message.answer("📝 Tavsifni matn bilan yozing yoki «-».")


@router.message(AdminProductStates.waiting_price)
async def hint_price(message: Message) -> None:
  await message.answer("🔢 Narxni raqam bilan yozing.")


@router.message(AdminProductStates.waiting_quantity)
async def hint_qty(message: Message) -> None:
  await message.answer("🔢 Miqdorni raqam bilan yozing.")


@router.message(AdminStockStates.waiting_quantity)
async def hint_stock_qty(message: Message) -> None:
  await message.answer("🔢 Kirim miqdorini raqam bilan yozing.")


@router.message(AdminEditStates.waiting_name)
async def hint_edit_name(message: Message) -> None:
  await message.answer("📝 Yangi nomni matn bilan yozing.")


@router.message(AdminEditStates.waiting_price)
async def hint_edit_price(message: Message) -> None:
  await message.answer("🔢 Yangi narxni raqam bilan yozing.")


@router.message(AdminEditStates.waiting_quantity)
async def hint_edit_qty(message: Message) -> None:
  await message.answer("🔢 Yangi miqdorni raqam bilan yozing.")
