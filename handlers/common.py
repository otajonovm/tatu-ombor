from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.start import is_admin
from keyboards import main_menu_keyboard

router = Router()


@router.message(F.text, ~F.text.startswith("/"))
async def fallback_text(message: Message, state: FSMContext) -> None:
  current = await state.get_state()
  if current:
    return

  await message.answer(
    "ℹ️ Tugmalardan foydalaning. Asosiy menyu:",
    reply_markup=main_menu_keyboard(is_admin(message.from_user.id)),
  )
