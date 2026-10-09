import logging
import re
import time
from io import BytesIO
from pathlib import Path

from aiogram import Bot

from supabase_db import upload_product_image

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent / "images"


def slugify(name: str) -> str:
  text = name.lower().strip()
  text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
  text = re.sub(r"[\s_-]+", "_", text)
  return text.strip("_") or "mahsulot"


def make_image_filename(product_name: str) -> str:
  return f"{slugify(product_name)}_{int(time.time())}.jpg"


async def save_telegram_photo(bot: Bot, file_id: str, product_name: str) -> str:
  """Download Telegram photo and upload to Supabase Storage.

  Returns a public HTTPS URL stored in products.image_url.
  Falls back to local images/ only if Storage upload fails (local/dev).
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
      "Supabase Storage'ga yuklanmadi, lokal saqlanadi: %s", error
    )
    IMAGES_DIR.mkdir(exist_ok=True)
    path = IMAGES_DIR / filename
    path.write_bytes(content)
    return filename
