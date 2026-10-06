"""Mahsulot deep-link QR kod generatsiyasi (xotirada, BytesIO)."""

from __future__ import annotations

import io

import qrcode
from qrcode.constants import ERROR_CORRECT_M

from config import BOT_USERNAME


def product_deep_link(product_id: int, bot_username: str | None = None) -> str:
  username = (bot_username or BOT_USERNAME).lstrip("@").strip()
  if not username:
    username = "tatubrandshopbot"
  return f"https://t.me/{username}?start=prod_{int(product_id)}"


def build_product_qr_png(product_id: int, bot_username: str | None = None) -> io.BytesIO:
  """Deep link uchun PNG QR kodni BytesIO da qaytaradi (seek=0)."""
  link = product_deep_link(product_id, bot_username)
  qr = qrcode.QRCode(
    version=None,
    error_correction=ERROR_CORRECT_M,
    box_size=10,
    border=2,
  )
  qr.add_data(link)
  qr.make(fit=True)
  image = qr.make_image(fill_color="black", back_color="white")

  buffer = io.BytesIO()
  image.save(buffer, format="PNG")
  buffer.seek(0)
  buffer.name = f"tatu_prod_{product_id}.png"
  return buffer
