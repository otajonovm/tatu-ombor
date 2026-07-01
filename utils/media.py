from pathlib import Path

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto, Message

from db import get_all_products

IMAGES_DIR = Path(__file__).parent.parent / "images"


def get_image_path(product: dict) -> Path | None:
  filename = product.get("image_path")
  if not filename:
    return None
  path = IMAGES_DIR / filename
  return path if path.is_file() else None


def product_status_icon(quantity: int) -> str:
  if quantity > 10:
    return "✅"
  if quantity > 0:
    return "⚠️"
  return "❌"


def product_status_text(quantity: int) -> str:
  if quantity > 10:
    return "Yetarli"
  if quantity > 0:
    return "Kam qolgan"
  return "Tugagan"


def gift_select_caption(product: dict) -> str:
  return (
    f"🎁 <b>Sovg'a berish</b>\n\n"
    f"📦 Mahsulot: <b>{product['name']}</b>\n"
    f"📊 Omborda: <b>{product['quantity']}</b> dona\n\n"
    f"🔢 <b>Nechta beriladi?</b> Raqam kiriting:"
  )


def product_caption(product: dict, *, detailed: bool = False) -> str:
  qty = product["quantity"]
  icon = product_status_icon(qty)

  if detailed:
    return (
      f"📦 <b>{product['name']}</b>\n\n"
      f"Qoldiq: <b>{qty}</b> dona\n"
      f"Holat: {product_status_text(qty)}"
    )

  return f"{icon} <b>{product['name']}</b>\nQoldiq: <b>{qty}</b> dona"


def stock_summary_text() -> str:
  products = get_all_products()
  if not products:
    return "📦 Hozircha omborda mahsulot yo'q."

  lines = ["📦 <b>Ombor qoldiqlari:</b>\n"]
  for product in products:
    icon = product_status_icon(product["quantity"])
    lines.append(
      f"{icon} <b>{product['name']}</b> — {product['quantity']} dona"
    )
  return "\n".join(lines)


async def replace_with_text(
  message: Message,
  text: str,
  reply_markup,
) -> Message:
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


async def send_product_photo(
  message: Message,
  product: dict,
  reply_markup,
  *,
  detailed: bool = False,
  caption: str | None = None,
) -> Message:
  path = get_image_path(product)
  text = caption or product_caption(product, detailed=detailed)

  if path:
    try:
      await message.delete()
    except TelegramBadRequest:
      pass

    return await message.answer_photo(
      photo=FSInputFile(path),
      caption=text,
      reply_markup=reply_markup,
    )

  return await replace_with_text(message, text, reply_markup)


async def show_sklad_menu(message: Message) -> None:
  from keyboards import sklad_keyboard

  products = get_all_products()
  if not products:
    await replace_with_text(message, "📦 Hozircha omborda mahsulot yo'q.", sklad_keyboard())
    return

  await replace_with_text(
    message,
    "🏪 <b>Ombor ro'yxati</b>\n\n"
    "Mahsulotni bosing — rasm va qoldiq chiqadi:",
    sklad_keyboard(),
  )


async def send_sklad_gallery(message: Message) -> None:
  from keyboards import sklad_keyboard

  products = get_all_products()
  if not products:
    await message.answer("📦 Hozircha omborda mahsulot yo'q.")
    return

  media: list[InputMediaPhoto] = []
  for product in products:
    path = get_image_path(product)
    if path:
      media.append(
        InputMediaPhoto(
          media=FSInputFile(path),
          caption=product_caption(product),
        )
      )

  if media:
    for index in range(0, len(media), 10):
      await message.answer_media_group(media[index : index + 10])

  if not media:
    lines = ["🏪 <b>Ombor — mahsulotlar:</b>\n"]
    for product in products:
      icon = product_status_icon(product["quantity"])
      lines.append(
        f"{icon} <b>{product['name']}</b> — {product['quantity']} dona"
      )
    await message.answer("\n".join(lines))

  await message.answer(
    "👇 Mahsulotni tanlang:",
    reply_markup=sklad_keyboard(),
  )


async def handle_callback_message(
  callback: CallbackQuery,
  text: str,
  reply_markup,
) -> None:
  await callback.answer()
  await replace_with_text(callback.message, text, reply_markup)
