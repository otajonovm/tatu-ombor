from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from filters.admin import is_admin


class AdminSecurityMiddleware(BaseMiddleware):
  """
  Admin router uchun qo'shimcha himoya.
  Filtr o'tkazib yuborgan bo'lsa ham, noadminlarga ruxsat bermaydi.
  """

  async def __call__(
    self,
    handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: dict[str, Any],
  ) -> Any:
    user = getattr(event, "from_user", None)
    user_id = user.id if user else None

    if not is_admin(user_id):
      if isinstance(event, CallbackQuery):
        await event.answer("⛔ Ruxsat yo'q!", show_alert=True)
      elif isinstance(event, Message):
        await event.answer("⛔ Bu amal faqat adminlar uchun.")
      return None

    return await handler(event, data)
