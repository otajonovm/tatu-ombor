r"""Telegram Mini App API.

The browser never receives a Supabase key. Every request must include the
Telegram WebApp initData header, which is verified with BOT_TOKEN here.
Run with: .venv\Scripts\python.exe -m uvicorn web_api:app --host 0.0.0.0 --port 8000
"""

import asyncio
import hashlib
import hmac
import json
import logging
from pathlib import Path
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qsl, unquote

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from config import ADMIN_IDS, BOT_TOKEN, TMA_DEV_MODE, WEBAPI_URL, WEBAPP_ORIGINS
from supabase_db import (
  add_product,
  approve_order,
  create_order,
  format_price,
  get_active_products,
  get_all_products,
  get_order,
  get_order_items,
  get_orders_by_status,
  get_user_orders,
  reject_order,
  stock_in,
  upload_product_image,
  update_product,
)
from supabase_db import IMAGES_DIR

from aiogram import Bot

logger = logging.getLogger(__name__)
app = FastAPI(title="TATU Brend Do'koni TMA API", version="1.0.0")
app.add_middleware(
  CORSMiddleware,
  allow_origins=WEBAPP_ORIGINS or ["*"],
  allow_credentials=False,
  allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
  allow_headers=["*"],
)
if Path(IMAGES_DIR).is_dir():
  app.mount("/media", StaticFiles(directory=IMAGES_DIR), name="media")


@dataclass(frozen=True)
class TelegramUser:
  id: int
  first_name: str
  last_name: str = ""
  username: str | None = None

  @property
  def full_name(self) -> str:
    return f"{self.first_name} {self.last_name}".strip()


def validate_telegram_init_data(
  init_data: str,
  *,
  max_age_seconds: int = 86_400,
) -> TelegramUser:
  """Verify Telegram WebApp initData per Telegram's HMAC-SHA256 algorithm."""
  if not init_data or not BOT_TOKEN:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram initData mavjud emas.",
    )

  pairs = dict(parse_qsl(init_data, keep_blank_values=True))
  received_hash = pairs.pop("hash", None)
  if not received_hash:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram imzosi mavjud emas.",
    )

  data_check_string = "\n".join(
    f"{key}={value}" for key, value in sorted(pairs.items())
  )
  secret_key = hmac.new(
    b"WebAppData",
    BOT_TOKEN.encode("utf-8"),
    hashlib.sha256,
  ).digest()
  calculated_hash = hmac.new(
    secret_key,
    data_check_string.encode("utf-8"),
    hashlib.sha256,
  ).hexdigest()

  if not hmac.compare_digest(calculated_hash, received_hash):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram initData imzosi noto'g'ri.",
    )

  try:
    auth_date = int(pairs.get("auth_date", "0"))
  except ValueError as error:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram auth_date noto'g'ri.",
    ) from error

  if auth_date <= 0 or time.time() - auth_date > max_age_seconds:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram initData eskirgan. Mini App'ni qayta oching.",
    )

  try:
    raw_user = json.loads(unquote(pairs["user"]))
    user = TelegramUser(
      id=int(raw_user["id"]),
      first_name=str(raw_user.get("first_name", "")),
      last_name=str(raw_user.get("last_name", "")),
      username=raw_user.get("username"),
    )
  except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Telegram user ma'lumotlari noto'g'ri.",
    ) from error

  return user


def telegram_user(
  x_telegram_init_data: str | None = Header(default=None),
) -> TelegramUser:
  init_data = (x_telegram_init_data or "").strip()
  if not init_data and TMA_DEV_MODE:
    # localhost Vite/brauzer: Telegram WebApp initData bo'lmaydi.
    admin_id = ADMIN_IDS[0] if ADMIN_IDS else 1
    logger.warning(
      "TMA_DEV_MODE: initData yo'q — mock user id=%s ishlatilmoqda.",
      admin_id,
    )
    return TelegramUser(
      id=admin_id,
      first_name="Dev",
      last_name="Admin",
      username="dev_admin",
    )
  return validate_telegram_init_data(init_data)


def admin_user(user: TelegramUser = Depends(telegram_user)) -> TelegramUser:
  if user.id not in ADMIN_IDS:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Bu amal faqat adminlar uchun.",
    )
  return user


async def run_db(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
  return await asyncio.to_thread(function, *args, **kwargs)


def public_product_image_urls(product: dict) -> dict:
  """Local bot images are exposed through the API for the Mini App."""
  result = dict(product)
  for key in ("image_url",):
    value = result.get(key)
    if value and not str(value).startswith(("http://", "https://")):
      result[key] = f"{WEBAPI_URL}/media/{value}"
  values = result.get("image_urls") or []
  result["image_urls"] = [
    value
    if str(value).startswith(("http://", "https://"))
    else f"{WEBAPI_URL}/media/{value}"
    for value in values
  ]
  return result


class OrderItemInput(BaseModel):
  product_id: int = Field(gt=0)
  quantity: int = Field(gt=0, le=100)
  size: str | None = Field(default=None, max_length=20)
  color: str | None = Field(default=None, max_length=40)


class OrderInput(BaseModel):
  phone_number: str = Field(min_length=7, max_length=30)
  comment: str = Field(default="", max_length=500)
  items: list[OrderItemInput] = Field(min_length=1, max_length=50)

  @field_validator("phone_number")
  @classmethod
  def validate_phone(cls, value: str) -> str:
    cleaned = value.strip()
    allowed = set("0123456789+ ()-")
    if not cleaned or any(char not in allowed for char in cleaned):
      raise ValueError("Telefon raqam noto'g'ri. Masalan: +998901234567")
    digits = "".join(char for char in cleaned if char.isdigit())
    if len(digits) < 9:
      raise ValueError("Telefon raqamda kamida 9 ta raqam bo'lsin.")
    return cleaned

  @field_validator("items")
  @classmethod
  def clean_items(cls, value: list[OrderItemInput]) -> list[OrderItemInput]:
    cleaned: list[OrderItemInput] = []
    for item in value:
      size = (item.size or "").strip() or None
      color = (item.color or "").strip() or None
      cleaned.append(
        item.model_copy(update={"size": size, "color": color})
      )
    return cleaned


class ProductInput(BaseModel):
  name: str = Field(min_length=2, max_length=120)
  description: str = Field(default="", max_length=1_000)
  category: str = Field(default="suvenir", max_length=40)
  price: int = Field(ge=0)
  quantity: int = Field(default=0, ge=0)
  image_url: str | None = Field(default=None, max_length=2_000)
  image_urls: list[str] = Field(default_factory=list, max_length=10)
  sizes: list[str] = Field(default_factory=list, max_length=10)
  colors: list[str] = Field(default_factory=list, max_length=20)


class ProductPatch(BaseModel):
  name: str | None = Field(default=None, min_length=2, max_length=120)
  description: str | None = Field(default=None, max_length=1_000)
  category: str | None = Field(default=None, max_length=40)
  price: int | None = Field(default=None, ge=0)
  image_url: str | None = Field(default=None, max_length=2_000)
  image_urls: list[str] | None = Field(default=None, max_length=10)
  sizes: list[str] | None = Field(default=None, max_length=10)
  colors: list[str] | None = Field(default=None, max_length=20)
  is_active: bool | None = None


class StockInput(BaseModel):
  quantity: int = Field(gt=0, le=100_000)
  comment: str = Field(default="", max_length=500)


@app.post("/api/admin/images")
async def admin_upload_image(
  file: UploadFile = File(...),
  user: TelegramUser = Depends(admin_user),
) -> dict[str, str]:
  del user
  if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(status_code=415, detail="Faqat rasm fayli yuboring.")
  content = await file.read()
  if len(content) > 5 * 1024 * 1024:
    raise HTTPException(status_code=413, detail="Rasm hajmi 5 MB dan oshmasin.")
  try:
    url = await run_db(
      upload_product_image,
      content,
      file.filename or "product.jpg",
      file.content_type,
    )
  except Exception as error:
    logger.exception("Supabase Storage upload failed")
    raise HTTPException(
      status_code=502,
      detail="Rasmni Supabase Storage'ga yuklab bo'lmadi.",
    ) from error
  return {"url": url}


async def notify_admins(order: dict, items: list[dict]) -> None:
  text_lines = [
    f"🔔 <b>Yangi TMA buyurtma #{order['id']}</b>",
    f"👤 {order.get('user_name') or order['user_id']}",
    f"📞 {order['phone_number']}",
    f"💰 {format_price(order['total_price'])}",
  ]
  if order.get("comment"):
    text_lines.append(f"💬 {order['comment']}")
  text_lines.append("\n<b>Tarkibi:</b>")
  for item in items:
    variant = " ".join(
      part for part in (item.get("size"), item.get("color")) if part
    )
    suffix = f" ({variant})" if variant else ""
    text_lines.append(
      f"• {item['product_name']}{suffix} × {item['quantity']}"
    )
  text_lines.append("\nAdmin panelda tasdiqlang yoki rad eting.")
  bot = Bot(BOT_TOKEN)
  try:
    for admin_id in ADMIN_IDS:
      try:
        await bot.send_message(admin_id, "\n".join(text_lines))
      except Exception:
        logger.exception("Admin notification failed: %s", admin_id)
  finally:
    await bot.session.close()


@app.get("/health")
async def health() -> dict[str, str]:
  return {"status": "ok"}


@app.get("/api/me")
async def me(user: TelegramUser = Depends(telegram_user)) -> dict[str, Any]:
  return {
    "id": user.id,
    "first_name": user.first_name,
    "last_name": user.last_name,
    "username": user.username,
    "is_admin": user.id in ADMIN_IDS,
  }


@app.get("/api/products")
async def products(
  category: str | None = None,
  search: str | None = None,
  user: TelegramUser = Depends(telegram_user),
) -> list[dict]:
  del user
  rows = await run_db(get_active_products)
  if category:
    rows = [row for row in rows if row.get("category") == category]
  if search:
    needle = search.casefold().strip()
    rows = [
      row for row in rows
      if needle in row["name"].casefold()
      or needle in (row.get("description") or "").casefold()
    ]
  return [public_product_image_urls(row) for row in rows]


@app.get("/api/orders")
async def my_orders(
  user: TelegramUser = Depends(telegram_user),
) -> list[dict]:
  return await run_db(get_user_orders, user.id)


@app.post("/api/orders", status_code=status.HTTP_201_CREATED)
async def create_tma_order(
  payload: OrderInput,
  user: TelegramUser = Depends(telegram_user),
) -> dict:
  order = await run_db(
    create_order,
    user.id,
    user.full_name,
    payload.phone_number,
    [item.model_dump() for item in payload.items],
    payload.comment,
  )
  if not order:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail="Mahsulot qoldig'i yetarli emas yoki buyurtma yaratilmadi.",
    )
  items = await run_db(get_order_items, order["id"])
  await notify_admins(order, items)
  return {"order": order, "items": items}


@app.get("/api/admin/products")
async def admin_products(
  user: TelegramUser = Depends(admin_user),
) -> list[dict]:
  del user
  products = await run_db(get_all_products, True)
  return [public_product_image_urls(product) for product in products]


@app.post("/api/admin/products", status_code=status.HTTP_201_CREATED)
async def admin_add_product(
  payload: ProductInput,
  user: TelegramUser = Depends(admin_user),
) -> dict:
  return await run_db(
    add_product,
    payload.name,
    payload.description,
    payload.price,
    payload.quantity,
    payload.image_url,
    user.id,
    payload.category,
    payload.image_urls,
    payload.sizes,
    payload.colors,
  )


@app.patch("/api/admin/products/{product_id}")
async def admin_update_product(
  product_id: int,
  payload: ProductPatch,
  user: TelegramUser = Depends(admin_user),
) -> dict:
  del user
  updates = payload.model_dump(exclude_unset=True)
  product = await run_db(update_product, product_id, updates)
  if not product:
    raise HTTPException(status_code=404, detail="Mahsulot topilmadi.")
  return product


@app.post("/api/admin/products/{product_id}/stock")
async def admin_stock(
  product_id: int,
  payload: StockInput,
  user: TelegramUser = Depends(admin_user),
) -> dict:
  product = await run_db(
    stock_in,
    product_id,
    payload.quantity,
    user.id,
    payload.comment or None,
  )
  if not product:
    raise HTTPException(
      status_code=409,
      detail="Kirim amalga oshmadi yoki mahsulot faol emas.",
    )
  return product


@app.get("/api/admin/orders")
async def admin_orders(
  user: TelegramUser = Depends(admin_user),
) -> list[dict]:
  del user
  orders = await run_db(get_orders_by_status, "pending")
  for order in orders:
    order["items"] = await run_db(get_order_items, order["id"])
  return orders


@app.post("/api/admin/orders/{order_id}/approve")
async def admin_approve(
  order_id: int,
  user: TelegramUser = Depends(admin_user),
) -> dict[str, Any]:
  ok, message = await run_db(approve_order, order_id, user.id)
  if not ok:
    raise HTTPException(status_code=409, detail=message)
  order = await run_db(get_order, order_id)
  return {"message": message, "order": order}


@app.post("/api/admin/orders/{order_id}/reject")
async def admin_reject(
  order_id: int,
  user: TelegramUser = Depends(admin_user),
) -> dict[str, Any]:
  ok, message = await run_db(reject_order, order_id)
  if not ok:
    raise HTTPException(status_code=409, detail=message)
  order = await run_db(get_order, order_id)
  return {"message": message, "order": order}
