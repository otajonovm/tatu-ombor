from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db import get_all_products, get_product, update_quantity
from handlers.start import is_admin
from keyboards import (
  cancel_keyboard,
  confirm_keyboard,
  gift_confirm_keyboard,
  main_menu_keyboard,
  product_detail_keyboard,
  products_keyboard,
)
from states import StockStates
from utils.media import (
  gift_select_caption,
  handle_callback_message,
  replace_with_text,
  send_product_photo,
  send_sklad_gallery,
  show_sklad_menu,
  stock_summary_text,
)

router = Router()

ACTION_LABELS = {
  "in": "Kirim qilish",
  "out": "Sovg'a berish",
  "check": "Qoldiqni tekshirish",
}


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
  await callback.answer("Mahsulotlar mavjud emas.", show_alert=True)


@router.callback_query(F.data == "menu:main")
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
  await state.clear()
  await handle_callback_message(
    callback,
    "📋 <b>Asosiy menyu</b>\n\nKerakli amalni tanlang:",
    main_menu_keyboard(is_admin(callback.from_user.id)),
  )


@router.callback_query(F.data.startswith("action:"))
async def handle_action(callback: CallbackQuery, state: FSMContext) -> None:
  action = callback.data.split(":")[1]
  await callback.answer()

  if action == "sklad":
    await show_sklad_menu(callback.message)
    return

  if action == "check":
    products = get_all_products()
    if not products:
      await replace_with_text(
        callback.message,
        "📦 Hozircha omborda mahsulot yo'q.",
        main_menu_keyboard(is_admin(callback.from_user.id)),
      )
      return

    await replace_with_text(
      callback.message,
      stock_summary_text(),
      main_menu_keyboard(is_admin(callback.from_user.id)),
    )
    return

  await state.clear()
  label = ACTION_LABELS.get(action, action)
  await replace_with_text(
    callback.message,
    f"<b>{label}</b>\n\nMahsulotni tanlang:",
    products_keyboard(action),
  )


@router.callback_query(F.data.startswith("detail:"))
async def product_detail(callback: CallbackQuery) -> None:
  product_id = int(callback.data.split(":")[1])
  product = get_product(product_id)

  if not product:
    await callback.answer("Mahsulot topilmadi.", show_alert=True)
    return

  await callback.answer()
  await send_product_photo(
    callback.message,
    product,
    product_detail_keyboard(product_id),
    detailed=True,
  )


@router.callback_query(F.data.startswith("product:"))
async def select_product(callback: CallbackQuery, state: FSMContext) -> None:
  parts = callback.data.split(":")
  action = parts[1]
  product_id = int(parts[2])
  product = get_product(product_id)

  if not product:
    await callback.answer("Mahsulot topilmadi.", show_alert=True)
    return

  if action == "out" and product["quantity"] <= 0:
    await callback.answer(
      f"«{product['name']}» tugagan! Kirim qiling.",
      show_alert=True,
    )
    return

  await callback.answer()

  if action == "out":
    await state.set_state(StockStates.waiting_quantity)
    await state.update_data(action=action, product_id=product_id)
    await send_product_photo(
      callback.message,
      product,
      cancel_keyboard(),
      caption=gift_select_caption(product),
    )
    return

  await state.set_state(StockStates.waiting_quantity)
  await state.update_data(action=action, product_id=product_id)

  await replace_with_text(
    callback.message,
    f"📦 <b>{product['name']}</b>\n"
    f"Hozirgi qoldiq: <b>{product['quantity']}</b> dona\n\n"
    f"Kirim miqdorini kiriting (faqat raqam):",
    cancel_keyboard(),
  )


@router.message(StockStates.waiting_quantity, F.text)
async def process_quantity(message: Message, state: FSMContext) -> None:
  current = await state.get_state()
  if not current or not current.startswith("StockStates:waiting_quantity"):
    return

  text = message.text.strip()

  if not text.isdigit() or int(text) <= 0:
    await message.answer(
      "❌ Noto'g'ri miqdor. Faqat musbat raqam kiriting:",
      reply_markup=cancel_keyboard(),
    )
    return

  quantity = int(text)
  data = await state.get_data()
  action = data["action"]
  product_id = data["product_id"]
  product = get_product(product_id)

  if not product:
    await state.clear()
    await message.answer("Mahsulot topilmadi.")
    return

  if action == "out" and quantity > product["quantity"]:
    await message.answer(
      f"❌ Omborda faqat <b>{product['quantity']}</b> dona bor.\n"
      "Kamroq miqdor kiriting:",
      reply_markup=cancel_keyboard(),
      parse_mode="HTML",
    )
    return

  if action == "out":
    await state.update_data(quantity=quantity)
    await state.set_state(StockStates.waiting_recipient)
    await message.answer(
      f"👤 <b>Kimga beriladi?</b>\n\n"
      f"Mahsulot: <b>{product['name']}</b>\n"
      f"Miqdor: <b>{quantity}</b> dona\n\n"
      "Qabul qiluvchi ismini kiriting (F.I.Sh):",
      reply_markup=cancel_keyboard(),
      parse_mode="HTML",
    )
    return

  await message.answer(
    f"📋 <b>Tasdiqlash</b>\n\n"
    f"Amal: Kirim\n"
    f"Mahsulot: <b>{product['name']}</b>\n"
    f"Miqdor: <b>+{quantity}</b> dona\n"
    f"Yangi qoldiq: <b>{product['quantity'] + quantity}</b> dona",
    reply_markup=confirm_keyboard(action, product_id, quantity),
    parse_mode="HTML",
  )


@router.message(StockStates.waiting_recipient, F.text)
async def process_recipient(message: Message, state: FSMContext) -> None:
  recipient = message.text.strip()

  if len(recipient) < 2:
    await message.answer(
      "❌ Ism juda qisqa. Qayta kiriting:",
      reply_markup=cancel_keyboard(),
    )
    return

  data = await state.get_data()
  product_id = data["product_id"]
  quantity = data["quantity"]
  product = get_product(product_id)

  if not product:
    await state.clear()
    await message.answer("Mahsulot topilmadi.")
    return

  if quantity > product["quantity"]:
    await state.clear()
    await message.answer(
      f"❌ Omborda endi faqat <b>{product['quantity']}</b> dona qoldi.",
      parse_mode="HTML",
    )
    return

  await state.update_data(recipient_name=recipient)

  await message.answer(
    f"📋 <b>Sovg'ani tasdiqlang</b>\n\n"
    f"📦 Mahsulot: <b>{product['name']}</b>\n"
    f"👤 Kimga: <b>{recipient}</b>\n"
    f"🔢 Miqdor: <b>{quantity}</b> dona\n"
    f"📊 Omborda qoladi: <b>{product['quantity'] - quantity}</b> dona",
    reply_markup=gift_confirm_keyboard(),
    parse_mode="HTML",
  )


@router.callback_query(F.data == "confirm:gift")
async def confirm_gift(callback: CallbackQuery, state: FSMContext) -> None:
  data = await state.get_data()
  product_id = data.get("product_id")
  quantity = data.get("quantity")
  recipient = data.get("recipient_name")

  if not all([product_id, quantity, recipient]):
    await callback.answer("Ma'lumotlar topilmadi. Qaytadan boshlang.", show_alert=True)
    await state.clear()
    return

  product = get_product(product_id)
  if not product or quantity > product["quantity"]:
    await callback.answer("Omborda yetarli mahsulot yo'q!", show_alert=True)
    await state.clear()
    return

  user = callback.from_user
  user_name = user.full_name or user.username or str(user.id)

  result = update_quantity(
    product_id,
    -quantity,
    user.id,
    user_name,
    "out",
    recipient_name=recipient,
  )

  await state.clear()

  if not result:
    await callback.answer("Xatolik yuz berdi!", show_alert=True)
    return

  await callback.answer("✅ Saqlandi!")
  await replace_with_text(
    callback.message,
    f"🎁 <b>Sovg'a berildi!</b>\n\n"
    f"📦 Mahsulot: <b>{result['name']}</b>\n"
    f"👤 Kimga: <b>{recipient}</b>\n"
    f"🔢 Miqdor: <b>{quantity}</b> dona\n"
    f"📊 Omborda qoldi: <b>{result['quantity']}</b> dona",
    main_menu_keyboard(is_admin(callback.from_user.id)),
  )


@router.callback_query(F.data.startswith("confirm:in:"))
async def confirm_in(callback: CallbackQuery, state: FSMContext) -> None:
  parts = callback.data.split(":")
  product_id = int(parts[2])
  quantity = int(parts[3])

  user = callback.from_user
  user_name = user.full_name or user.username or str(user.id)

  result = update_quantity(product_id, quantity, user.id, user_name, "in")

  await state.clear()

  if not result:
    await callback.answer("Xatolik yuz berdi!", show_alert=True)
    return

  await callback.answer("✅ Saqlandi!")
  await replace_with_text(
    callback.message,
    f"➕ <b>Muvaffaqiyatli!</b>\n\n"
    f"<b>{result['name']}</b> — {quantity} dona kirim qilindi.\n"
    f"Joriy qoldiq: <b>{result['quantity']}</b> dona",
    main_menu_keyboard(is_admin(callback.from_user.id)),
  )
