from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from db import add_product, delete_product, get_product_by_name, get_recent_transactions
from handlers.start import is_admin
from keyboards import admin_delete_keyboard, admin_panel_keyboard, cancel_keyboard, main_menu_keyboard
from states import AdminStates
from utils.files import IMAGES_DIR, save_telegram_photo
from utils.media import replace_with_text

router = Router()


@router.callback_query(F.data == "admin:panel")
async def admin_panel(callback: CallbackQuery) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  await callback.answer()
  await replace_with_text(
    callback.message,
    "⚙️ <b>Admin panel</b>\n\nKerakli amalni tanlang:",
    admin_panel_keyboard(),
  )


@router.callback_query(F.data == "admin:add_product")
async def admin_add_product(callback: CallbackQuery, state: FSMContext) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  await callback.answer()
  await state.clear()
  await state.set_state(AdminStates.waiting_product_name)
  await replace_with_text(
    callback.message,
    "➕ <b>Yangi mahsulot — 1/3</b>\n\n"
    "Mahsulot nomini kiriting:",
    cancel_keyboard(),
  )


@router.message(AdminStates.waiting_product_name, F.text)
async def process_new_product_name(message: Message, state: FSMContext) -> None:
  if not is_admin(message.from_user.id):
    await state.clear()
    await message.answer("Ruxsat yo'q.")
    return

  if message.text.startswith("/"):
    await message.answer(
      "❌ Buyruq emas, mahsulot <b>nomini</b> yozing:",
      reply_markup=cancel_keyboard(),
    )
    return

  name = message.text.strip()
  if len(name) < 2:
    await message.answer(
      "❌ Nom juda qisqa. Qayta kiriting:",
      reply_markup=cancel_keyboard(),
    )
    return

  if name.isdigit():
    await message.answer(
      "❌ Nom faqat raqam bo'lmasligi kerak. Qayta kiriting:",
      reply_markup=cancel_keyboard(),
    )
    return

  if get_product_by_name(name):
    await message.answer(
      "❌ Bu nomdagi mahsulot allaqachon mavjud.",
      reply_markup=cancel_keyboard(),
    )
    return

  await state.update_data(new_product_name=name)
  await state.set_state(AdminStates.waiting_product_quantity)
  await message.answer(
    f"➕ <b>Yangi mahsulot — 2/3</b>\n\n"
    f"📦 Mahsulot: <b>{name}</b>\n\n"
    "Omborga nechta dona qo'shiladi? Raqam kiriting:",
    reply_markup=cancel_keyboard(),
  )


@router.message(AdminStates.waiting_product_quantity, F.text)
async def process_new_product_quantity(message: Message, state: FSMContext) -> None:
  if not is_admin(message.from_user.id):
    await state.clear()
    await message.answer("Ruxsat yo'q.")
    return

  if message.text.startswith("/"):
    await message.answer(
      "❌ Miqdorni raqam bilan yozing:",
      reply_markup=cancel_keyboard(),
    )
    return

  text = message.text.strip()
  if not text.isdigit() or int(text) < 0:
    await message.answer(
      "❌ Noto'g'ri miqdor. 0 yoki undan katta raqam kiriting:",
      reply_markup=cancel_keyboard(),
    )
    return

  quantity = int(text)
  data = await state.get_data()
  name = data.get("new_product_name", "")

  await state.update_data(new_product_quantity=quantity)
  await state.set_state(AdminStates.waiting_product_image)
  await message.answer(
    f"➕ <b>Yangi mahsulot — 3/3</b>\n\n"
    f"📦 Mahsulot: <b>{name}</b>\n"
    f"📊 Miqdor: <b>{quantity}</b> dona\n\n"
    "📷 Mahsulot rasmini yuboring (foto sifatida):",
    reply_markup=cancel_keyboard(),
  )


@router.message(AdminStates.waiting_product_image, F.photo)
async def process_new_product_image(message: Message, state: FSMContext) -> None:
  if not is_admin(message.from_user.id):
    await state.clear()
    return

  data = await state.get_data()
  name = data.get("new_product_name")
  quantity = data.get("new_product_quantity", 0)

  if not name:
    await state.clear()
    await message.answer("Xatolik. Qaytadan boshlang.")
    return

  if get_product_by_name(name):
    await state.clear()
    await message.answer("❌ Bu mahsulot allaqachon mavjud.")
    return

  photo = message.photo[-1]
  try:
    image_path = await save_telegram_photo(message.bot, photo.file_id, name)
    product = add_product(name, quantity, image_path)
  except Exception:
    await message.answer(
      "❌ Rasmni saqlab bo'lmadi. Qayta yuboring:",
      reply_markup=cancel_keyboard(),
    )
    return

  await state.clear()
  await message.answer_photo(
    photo=FSInputFile(IMAGES_DIR / image_path),
    caption=(
      f"✅ <b>Mahsulot qo'shildi!</b>\n\n"
      f"📦 Nomi: <b>{product['name']}</b>\n"
      f"📊 Miqdor: <b>{product['quantity']}</b> dona\n"
      f"🆔 ID: {product['id']}"
    ),
    reply_markup=main_menu_keyboard(is_admin=True),
  )


@router.message(AdminStates.waiting_product_image)
async def process_new_product_image_invalid(message: Message) -> None:
  await message.answer(
    "❌ Iltimos, mahsulot rasmini <b>foto</b> sifatida yuboring.",
    reply_markup=cancel_keyboard(),
  )


@router.callback_query(F.data == "admin:delete_list")
async def admin_delete_list(callback: CallbackQuery) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  await callback.answer()
  await replace_with_text(
    callback.message,
    "🗑 O'chiriladigan mahsulotni tanlang:",
    admin_delete_keyboard(),
  )


@router.callback_query(F.data.startswith("admin:delete:"))
async def admin_delete_product(callback: CallbackQuery) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  product_id = int(callback.data.split(":")[2])
  if delete_product(product_id):
    await callback.answer("Mahsulot o'chirildi!", show_alert=True)
  else:
    await callback.answer("Mahsulot topilmadi.", show_alert=True)

  await replace_with_text(
    callback.message,
    "🗑 O'chiriladigan mahsulotni tanlang:",
    admin_delete_keyboard(),
  )


@router.callback_query(F.data == "admin:history")
async def admin_history(callback: CallbackQuery) -> None:
  if not is_admin(callback.from_user.id):
    await callback.answer("Ruxsat yo'q!", show_alert=True)
    return

  await callback.answer()

  transactions = get_recent_transactions(15)

  if not transactions:
    text = "📊 Hozircha harakatlar yo'q."
  else:
    lines = ["📊 <b>So'nggi harakatlar:</b>\n"]
    for t in transactions:
      emoji = "➕" if t["action"] == "in" else "🎁"
      giver = t.get("user_name") or "Noma'lum"
      lines.append(
        f"{emoji} {t['created_at']}\n"
        f"   {t['product_name']} — {t['amount']} dona\n"
      )
      if t["action"] == "out" and t.get("recipient_name"):
        lines.append(f"   👤 Kimga: {t['recipient_name']}\n")
      lines.append(f"   🧑 Berdi: {giver}\n")
    text = "\n".join(lines)

  await replace_with_text(
    callback.message,
    text,
    admin_panel_keyboard(),
  )


@router.message(AdminStates.waiting_product_name)
async def waiting_product_name_hint(message: Message) -> None:
  await message.answer(
    "📝 Mahsulot <b>nomini</b> matn ko'rinishida yozing:",
    reply_markup=cancel_keyboard(),
  )


@router.message(AdminStates.waiting_product_quantity)
async def waiting_product_quantity_hint(message: Message) -> None:
  await message.answer(
    "🔢 Miqdorni <b>raqam</b> bilan yozing (masalan: 50):",
    reply_markup=cancel_keyboard(),
  )
