from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from keyboards import main_menu_keyboard

router = Router()

WELCOME_TEXT = (
  "🏛 <b>TATU Ombor nazorati</b>\n\n"
  "Xush kelibsiz! Quyidagi tugmalardan foydalaning.\n"
  "Faqat miqdor kiritishda matn yozishingiz kerak bo'ladi."
)


def is_admin(user_id: int) -> bool:
  return user_id in ADMIN_IDS


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
  await state.clear()
  await message.answer(
    WELCOME_TEXT,
    reply_markup=main_menu_keyboard(is_admin(message.from_user.id)),
    parse_mode="HTML",
  )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext) -> None:
  await state.clear()
  await message.answer(
    "📋 <b>Asosiy menyu</b>",
    reply_markup=main_menu_keyboard(is_admin(message.from_user.id)),
    parse_mode="HTML",
  )


@router.message(Command("sklad"))
async def cmd_sklad(message: Message) -> None:
  from utils.media import send_sklad_gallery

  await send_sklad_gallery(message)
