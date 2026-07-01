import re
import time
from pathlib import Path

from aiogram import Bot

IMAGES_DIR = Path(__file__).parent.parent / "images"


def slugify(name: str) -> str:
  text = name.lower().strip()
  text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
  text = re.sub(r"[\s_-]+", "_", text)
  return text.strip("_") or "mahsulot"


def make_image_filename(product_name: str) -> str:
  return f"{slugify(product_name)}_{int(time.time())}.jpg"


async def save_telegram_photo(bot: Bot, file_id: str, product_name: str) -> str:
  IMAGES_DIR.mkdir(exist_ok=True)
  filename = make_image_filename(product_name)
  path = IMAGES_DIR / filename

  file = await bot.get_file(file_id)
  await bot.download_file(file.file_path, path)
  return filename
