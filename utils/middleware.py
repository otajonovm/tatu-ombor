from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.fsm.context import FSMContext


class AdminFlowGuard(BaseMiddleware):
  """Admin mahsulot qo'shish jarayonida stock handlerlar ishlamasin."""

  async def __call__(
    self,
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
  ) -> Any:
    state: FSMContext | None = data.get("state")
    if state:
      current = await state.get_state()
      if current and current.startswith("AdminStates:"):
        if isinstance(event, CallbackQuery):
          await event.answer(
            "⚠️ Avval mahsulot qo'shishni tugating yoki Bekor qiling.",
            show_alert=True,
          )
        return None
    return await handler(event, data)


class StockFlowGuard(BaseMiddleware):
  """Stock jarayonida admin handlerlar aralashmasin."""

  async def __call__(
    self,
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
  ) -> Any:
    state: FSMContext | None = data.get("state")
    if state:
      current = await state.get_state()
      if current and current.startswith("StockStates:"):
        if isinstance(event, CallbackQuery):
          await event.answer(
            "⚠️ Avval joriy amalni tugating yoki Bekor qiling.",
            show_alert=True,
          )
        return None
    return await handler(event, data)
