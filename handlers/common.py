from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import SHOP_NAME
from filters.admin import is_admin
from keyboards import (
  BTN_ADMIN_MENU,
  BTN_CANCEL,
  BTN_CLIENT_MENU,
  admin_reply_keyboard,
  client_reply_keyboard,
  role_reply_keyboard,
)

router = Router(name="common")


def welcome_text(admin_user: bool) -> str:
  role = "Admin" if admin_user else "Mijoz"
  return (
    f"🏛 <b>{SHOP_NAME}</b>\n\n"
    f"Xush kelibsiz! Sizning rolingiz: <b>{role}</b>\n"
    "Pastdagi menyudan foydalaning."
  )


@router.message(Command("start", "menu"))
async def cmd_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    welcome_text(admin_user),
    reply_markup=role_reply_keyboard(admin_user),
  )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
  admin_user = is_admin(message.from_user.id)
  if admin_user:
    text = (
      "⚙️ <b>Admin yordam</b>\n\n"
      "• Mahsulot qo'shish / kirim / boshqarish\n"
      "• Yangi buyurtmalarni tasdiqlash yoki rad etish\n"
      "• Statistika va tarix\n"
      "• «Mijoz menyusi» orqali katalogni ko'rish"
    )
  else:
    text = (
      "ℹ️ <b>Yordam</b>\n\n"
      "• Katalogdan mahsulot tanlang\n"
      "• Savatga qo'shing yoki tezkor buyurtma bering\n"
      "• «Mening buyurtmalarim» orqali holatni kuzating"
    )
  await message.answer(text, reply_markup=role_reply_keyboard(admin_user))


@router.message(F.text == BTN_CLIENT_MENU)
async def switch_to_client_menu(message: Message, state: FSMContext) -> None:
  if not is_admin(message.from_user.id):
    await message.answer("⛔ Ruxsat yo'q.")
    return
  await state.clear()
  await message.answer(
    "🛍 Mijoz menyusi ochildi.\n"
    "Admin panelga qaytish: «⚙️ Admin menyu».",
    reply_markup=client_reply_keyboard(show_admin_back=True),
  )


@router.message(F.text == BTN_ADMIN_MENU)
async def switch_to_admin_menu(message: Message, state: FSMContext) -> None:
  if not is_admin(message.from_user.id):
    await message.answer("⛔ Ruxsat yo'q.")
    return
  await state.clear()
  await message.answer(
    "⚙️ Admin menyusi ochildi.",
    reply_markup=admin_reply_keyboard(),
  )


@router.message(F.text == BTN_CANCEL)
async def cancel_flow(message: Message, state: FSMContext) -> None:
  await state.clear()
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    "❌ Bekor qilindi.",
    reply_markup=role_reply_keyboard(admin_user),
  )


@router.callback_query(F.data.startswith("admin:"))
async def block_admin_callbacks(callback: CallbackQuery) -> None:
  """Admin routerdan o'tmagan admin:* callbacklar — mijoz uchun taqiqlangan."""
  if is_admin(callback.from_user.id):
    await callback.answer()
    return
  await callback.answer("⛔ Admin amallariga ruxsat yo'q!", show_alert=True)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
  await callback.answer()


@router.message(F.text, ~F.text.startswith("/"))
async def fallback_text(message: Message, state: FSMContext) -> None:
  current = await state.get_state()
  if current:
    return
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    "ℹ️ Menyudagi tugmalardan foydalaning.",
    reply_markup=role_reply_keyboard(admin_user),
  )
