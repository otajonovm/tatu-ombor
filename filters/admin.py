from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS


class IsAdminFilter(BaseFilter):
  """Faqat ADMIN_IDS dagi foydalanuvchilar uchun."""

  async def __call__(self, event: Message | CallbackQuery) -> bool:
    user = event.from_user
    return bool(user and user.id in ADMIN_IDS)


def is_admin(user_id: int | None) -> bool:
  return bool(user_id and user_id in ADMIN_IDS)
