import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import (
  BOT_TOKEN,
  CLICK_PROVIDER_TOKEN,
  DEFAULT_PRODUCTS,
  PAYME_PROVIDER_TOKEN,
  SUPABASE_KEY,
  SUPABASE_URL,
)
from handlers import admin, client, common, payment
from supabase_db import init_db
from utils.placeholders import ensure_product_images
from utils.singleton import acquire_singleton, release_singleton

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
  if not BOT_TOKEN:
    logger.error("BOT_TOKEN .env faylida ko'rsatilmagan!")
    sys.exit(1)

  if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error(
      "SUPABASE_URL yoki SUPABASE_ANON_KEY .env faylida ko'rsatilmagan!"
    )
    sys.exit(1)

  acquire_singleton()

  try:
    logger.info("Supabase API ga ulanilmoqda...")
    init_db(DEFAULT_PRODUCTS)
    ensure_product_images(DEFAULT_PRODUCTS)

    bot = Bot(
      token=BOT_TOKEN,
      default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib: to'lov (pre_checkout/success), admin, mijoz, common
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(client.router)
    dp.include_router(common.router)

    for name, token in (
      ("Click", CLICK_PROVIDER_TOKEN),
      ("Payme", PAYME_PROVIDER_TOKEN),
    ):
      if token:
        mode = "TEST" if ":TEST:" in token else "LIVE"
        logger.info("%s to'lovlari yoqilgan (%s).", name, mode)
      else:
        logger.warning("%s tokeni yo'q — bu usul o'chirilgan.", name)

    logger.info("TATU Brend Do'kon boti ishga tushmoqda...")
    await dp.start_polling(bot, drop_pending_updates=True)
  finally:
    release_singleton()


if __name__ == "__main__":
  asyncio.run(main())
