from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import asyncio

from config import SHOP_NAME
from filters.admin import is_admin
from keyboards import (
  BTN_ADMIN_MENU,
  BTN_CLIENT_MENU,
  admin_reply_keyboard,
  client_reply_keyboard,
  product_buy_keyboard,
  role_reply_keyboard,
)
from handlers.orders import handle_claim_start, parse_claim_arg
from locales import button_values, t
from supabase_db import get_product, has_user_language
from utils.media import send_product_card

router = Router(name="common")


def welcome_text(admin_user: bool, lang: str) -> str:
  role = t(lang, "role_admin" if admin_user else "role_client")
  return t(lang, "welcome", shop=SHOP_NAME, role=role)


def parse_product_deep_link(args: str | None) -> int | None:
  """prod_15 → 15. Noto'g'ri format uchun None."""
  if not args:
    return None
  raw = args.strip()
  if not raw.startswith("prod_"):
    return None
  product_id = raw.removeprefix("prod_").strip()
  if not product_id.isdigit():
    return None
  return int(product_id)


async def resume_start(
  message: Message,
  args: str | None,
  lang: str,
  user_id: int | None = None,
) -> None:
  """Til tanlangach yoki til allaqachon saqlanganida /start davomi."""
  actor_id = user_id if user_id is not None else message.from_user.id
  admin_user = is_admin(actor_id)
  keyboard = role_reply_keyboard(admin_user, lang)
  claim_id = parse_claim_arg(args)
  if claim_id is not None:
    await handle_claim_start(message, claim_id, lang, actor_id)
    return

  product_id = parse_product_deep_link(args)
  if product_id is not None:
    product = get_product(product_id)
    if (
      not product
      or not product.get("is_active", True)
      or int(product.get("quantity") or 0) <= 0
    ):
      await message.answer(t(lang, "product_link_missing"), reply_markup=keyboard)
      return

    await message.answer(t(lang, "product_link_opened"), reply_markup=keyboard)
    await send_product_card(
      message,
      product,
      product_buy_keyboard(product_id, lang),
      for_client=True,
      lang=lang,
    )
    return

  await message.answer(welcome_text(admin_user, lang), reply_markup=keyboard)


@router.message(CommandStart())
async def cmd_start(
  message: Message,
  state: FSMContext,
  command: CommandObject,
  lang: str,
) -> None:
  await state.clear()
  known = await asyncio.to_thread(has_user_language, message.from_user.id)
  if not known:
    from handlers.language import ask_language

    await ask_language(message, state, command.args)
    return
  await resume_start(message, command.args, lang)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, lang: str) -> None:
  await state.clear()
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    welcome_text(admin_user, lang),
    reply_markup=role_reply_keyboard(admin_user, lang),
  )


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str) -> None:
  admin_user = is_admin(message.from_user.id)
  key = "help_admin" if admin_user else "help_client"
  await message.answer(
    t(lang, key),
    reply_markup=role_reply_keyboard(admin_user, lang),
  )


@router.message(F.text == BTN_CLIENT_MENU)
async def switch_to_client_menu(message: Message, state: FSMContext, lang: str) -> None:
  if not is_admin(message.from_user.id):
    await message.answer(t(lang, "no_permission"))
    return
  await state.clear()
  await message.answer(
    t(lang, "client_menu_opened"),
    reply_markup=client_reply_keyboard(show_admin_back=True, lang=lang),
  )


@router.message(F.text == BTN_ADMIN_MENU)
async def switch_to_admin_menu(message: Message, state: FSMContext, lang: str) -> None:
  if not is_admin(message.from_user.id):
    await message.answer(t(lang, "no_permission"))
    return
  await state.clear()
  await message.answer(
    t(lang, "admin_menu_opened"),
    reply_markup=admin_reply_keyboard(lang),
  )


@router.message(F.text.in_(button_values("btn_cancel")))
async def cancel_flow(message: Message, state: FSMContext, lang: str) -> None:
  await state.clear()
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    t(lang, "cancelled"),
    reply_markup=role_reply_keyboard(admin_user, lang),
  )


@router.callback_query(F.data.startswith("admin:"))
async def block_admin_callbacks(callback: CallbackQuery, lang: str) -> None:
  """Admin routerdan o'tmagan admin:* callbacklar — mijoz uchun taqiqlangan."""
  if is_admin(callback.from_user.id):
    await callback.answer()
    return
  await callback.answer(t(lang, "no_permission"), show_alert=True)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
  await callback.answer()


@router.message(F.text, ~F.text.startswith("/"))
async def fallback_text(message: Message, state: FSMContext, lang: str) -> None:
  current = await state.get_state()
  if current:
    return
  admin_user = is_admin(message.from_user.id)
  await message.answer(
    t(lang, "use_menu"),
    reply_markup=role_reply_keyboard(admin_user, lang),
  )
