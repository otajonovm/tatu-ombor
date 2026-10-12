"""Har bir yangilanishda foydalanuvchi tilini handlerga beradi."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from supabase_db import get_user_language


class LanguageMiddleware(BaseMiddleware):
  async def __call__(
    self,
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
  ) -> Any:
    user = data.get("event_from_user") or getattr(event, "from_user", None)
    lang = "uz"
    if user is not None:
      lang = await asyncio.to_thread(get_user_language, user.id)
    data["lang"] = lang
    return await handler(event, data)
