from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import FSInputFile, Message

from supabase_db import format_price

IMAGES_DIR = Path(__file__).parent.parent / "images"


def get_image_path(product: dict) -> Path | None:
  filename = product.get("image_url")
  if not filename:
    return None
  if str(filename).startswith("http"):
    return None
  path = IMAGES_DIR / filename
  return path if path.is_file() else None


def product_caption(product: dict, *, for_client: bool = True) -> str:
  lines = [
    f"🛍 <b>{product['name']}</b>",
    "",
  ]
  description = (product.get("description") or "").strip()
  if description:
    lines.extend([description, ""])
  lines.extend(
    [
      f"💰 Narx: <b>{format_price(product['price'])}</b>",
      f"📦 Qoldiq: <b>{product['quantity']}</b> dona",
    ]
  )
  if not for_client:
    status = "Faol" if product.get("is_active", True) else "Arxivlangan"
    lines.append(f"🔖 Holat: <b>{status}</b>")
  return "\n".join(lines)


async def replace_with_text(message: Message, text: str, reply_markup=None) -> Message:
  if message.photo or message.document:
    try:
      await message.delete()
    except TelegramBadRequest:
      pass
    return await message.answer(text, reply_markup=reply_markup)

  try:
    await message.edit_text(text, reply_markup=reply_markup)
    return message
  except TelegramBadRequest as error:
    if "message is not modified" in str(error).lower():
      return message
    return await message.answer(text, reply_markup=reply_markup)


async def send_product_card(
  message: Message,
  product: dict,
  reply_markup=None,
  *,
  for_client: bool = True,
) -> Message:
  path = get_image_path(product)
  caption = product_caption(product, for_client=for_client)

  if path:
    try:
      await message.delete()
    except TelegramBadRequest:
      pass
    return await message.answer_photo(
      photo=FSInputFile(path),
      caption=caption,
      reply_markup=reply_markup,
    )

  return await replace_with_text(message, caption, reply_markup)
