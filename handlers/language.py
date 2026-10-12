"""Birinchi tanlov va «Tilni o'zgartirish»."""

from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import language_keyboard
from locales import button_values, normalize_lang, t
from supabase_db import set_user_language

router = Router(name="language")


async def ask_language(message: Message, state: FSMContext, start_arg: str | None) -> None:
  await state.update_data(pending_start=(start_arg or "").strip())
  await message.answer(t("uz", "choose_language"), reply_markup=language_keyboard())


@router.message(F.text.in_(button_values("btn_language")))
async def on_change_language(message: Message, state: FSMContext) -> None:
  await state.update_data(pending_start="")
  await message.answer(t("uz", "choose_language"), reply_markup=language_keyboard())


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery, state: FSMContext) -> None:
  code = normalize_lang((callback.data or "").split(":", 1)[-1])
  if code not in {"uz", "ru", "en"}:
    await callback.answer()
    return
  try:
    await asyncio.to_thread(set_user_language, callback.from_user.id, code)
  except Exception:
    await callback.answer(t(code, "language_save_failed"), show_alert=True)
    return

  data = await state.get_data()
  pending = str(data.get("pending_start") or "")
  await state.clear()
  await callback.answer(t(code, "language_saved"))

  from handlers.common import resume_start

  if callback.message is not None:
    await resume_start(callback.message, pending, code, user_id=callback.from_user.id)
  else:
    await callback.bot.send_message(callback.from_user.id, t(code, "language_saved"))
