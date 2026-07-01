import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, DEFAULT_PRODUCTS
from db import cleanup_bad_products, fix_wrong_kirim, init_db
from handlers import admin, common, start, stock
from utils.middleware import AdminFlowGuard, StockFlowGuard
from utils.placeholders import ensure_product_images
from utils.singleton import acquire_singleton, release_singleton

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def main() -> None:
  if not BOT_TOKEN:
    logger.error("BOT_TOKEN .env faylida ko'rsatilmagan!")
    sys.exit(1)

  acquire_singleton()

  try:
    init_db(DEFAULT_PRODUCTS)
    removed = cleanup_bad_products({p["name"] for p in DEFAULT_PRODUCTS})
    if removed:
      logger.info("Noto'g'ri mahsulotlar o'chirildi: %s ta", removed)
    if fix_wrong_kirim("Bloknot", 2000):
      logger.info("Bloknot noto'g'ri qoldig'i tuzatildi")
    ensure_product_images(DEFAULT_PRODUCTS)

    bot = Bot(
      token=BOT_TOKEN,
      default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    stock.router.message.middleware(AdminFlowGuard())
    stock.router.callback_query.middleware(AdminFlowGuard())
    admin.router.message.middleware(StockFlowGuard())
    admin.router.callback_query.middleware(StockFlowGuard())

    dp.include_router(admin.router)
    dp.include_router(stock.router)
    dp.include_router(start.router)
    dp.include_router(common.router)

    logger.info("TATU Ombor boti ishga tushmoqda...")
    await dp.start_polling(bot, drop_pending_updates=True)
  finally:
    release_singleton()


if __name__ == "__main__":
  asyncio.run(main())
