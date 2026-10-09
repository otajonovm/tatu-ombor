import logging
import re
import time
from io import BytesIO
from pathlib import Path

from aiogram import Bot

from supabase_db import upload_product_image

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent / "images"
TG_FILE_PREFIX = "tgfile:"


def slugify(name: str) -> str:
  text = name.lower().strip()
  text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
  text = re.sub(r"[\s_-]+", "_", text)
  return text.strip("_") or "mahsulot"


def make_image_filename(product_name: str) -> str:
  return f"{slugify(product_name)}_{int(time.time())}.jpg"


async def save_telegram_photo(bot: Bot, file_id: str, product_name: str) -> str:
  """Download Telegram photo and upload to Supabase Storage.

  Returns a public HTTPS URL when Storage works.
  Falls back to tgfile:<file_id> so the bot can still show the photo later
  (Heroku disk is ephemeral, so local files are not used as fallback).
  """
  filename = make_image_filename(product_name)
  buffer = BytesIO()
  file = await bot.get_file(file_id)
  await bot.download_file(file.file_path, buffer)
  content = buffer.getvalue()
  if not content:
    raise RuntimeError("Bo'sh rasm fayli")

  try:
    return upload_product_image(content, filename, "image/jpeg")
  except Exception as error:
    logger.warning(
      "Supabase Storage'ga yuklanmadi, Telegram file_id saqlanadi: %s", error
    )
    return f"{TG_FILE_PREFIX}{file_id}"
