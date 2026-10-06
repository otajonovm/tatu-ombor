from pathlib import Path
from typing import Any
import logging
import uuid

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

IMAGES_DIR = Path(__file__).parent / "images"
PRODUCT_FIELDS = (
  "id,name,description,price,quantity,image_url,image_urls,category,"
  "sizes,colors,is_active,created_at"
)
ORDER_FIELDS = (
  "id,user_id,user_name,phone_number,comment,total_price,status,created_at"
)

_client: Client | None = None
_carts: dict[int, dict[int, int]] = {}
logger = logging.getLogger(__name__)


def _db() -> Client:
  global _client
  if _client is None:
    if not SUPABASE_URL or not SUPABASE_KEY:
      raise RuntimeError(
        "SUPABASE_URL va SUPABASE_ANON_KEY .env da ko'rsatilishi kerak."
      )
    _client = create_client(SUPABASE_URL, SUPABASE_KEY)
  return _client


def _one(data: Any) -> dict | None:
  if isinstance(data, list):
    return data[0] if data else None
  return data if isinstance(data, dict) else None


def init_db(default_products: list[dict]) -> None:
  """REST API orqali sxemani tekshiradi va standart mahsulotlarni qo'shadi."""
  try:
    existing = (
      _db().table("products").select("name").execute().data or []
    )
  except Exception as error:
    raise RuntimeError(
      "Supabase jadvallari topilmadi. Avval supabase/schema.sql faylini "
      "Supabase SQL Editor'da ishga tushiring."
    ) from error

  names = {row["name"] for row in existing}
  missing = [
    {
      "name": product["name"],
      "description": product.get("description", ""),
      "price": product.get("price", 0),
      "quantity": product.get("quantity", 0),
      "image_url": product.get("image"),
      "image_urls": product.get("image_urls", []),
      "category": product.get("category", "suvenir"),
      "sizes": product.get("sizes", []),
      "colors": product.get("colors", []),
    }
    for product in default_products
    if product["name"] not in names
  ]
  if missing:
    try:
      _db().table("products").insert(missing).execute()
    except Exception as error:
      logger.warning(
        "Supabase yozishni blokladi: %s. Yangilangan "
        "supabase/schema.sql faylini SQL Editor'da ishga tushiring.",
        error,
      )


def format_price(amount: int) -> str:
  return f"{int(amount):,}".replace(",", " ") + " so'm"


def upload_product_image(content: bytes, filename: str, content_type: str) -> str:
  extension = Path(filename).suffix.lower() or ".jpg"
  path = f"products/{uuid.uuid4().hex}{extension}"
  _db().storage.from_("product-images").upload(
    path,
    content,
    {"content-type": content_type, "upsert": "false"},
  )
  return _db().storage.from_("product-images").get_public_url(path)


# ── Products ───────────────────────────────────────────────


def get_active_products() -> list[dict]:
  response = (
    _db()
    .table("products")
    .select(PRODUCT_FIELDS)
    .eq("is_active", True)
    .gt("quantity", 0)
    .order("name")
    .execute()
  )
  return response.data or []


def get_all_products(include_inactive: bool = True) -> list[dict]:
  query = _db().table("products").select(PRODUCT_FIELDS)
  if not include_inactive:
    query = query.eq("is_active", True)
  response = query.order("name").execute()
  rows = response.data or []
  return sorted(rows, key=lambda row: (not row["is_active"], row["name"]))


def get_product(product_id: int) -> dict | None:
  response = (
    _db()
    .table("products")
    .select(PRODUCT_FIELDS)
    .eq("id", product_id)
    .limit(1)
    .execute()
  )
  return _one(response.data)


def get_product_by_name(name: str) -> dict | None:
  response = (
    _db()
    .table("products")
    .select(PRODUCT_FIELDS)
    .eq("name", name.strip())
    .limit(1)
    .execute()
  )
  return _one(response.data)


def add_product(
  name: str,
  description: str,
  price: int,
  quantity: int = 0,
  image_url: str | None = None,
  admin_id: int | None = None,
  category: str = "suvenir",
  image_urls: list[str] | None = None,
  sizes: list[str] | None = None,
  colors: list[str] | None = None,
) -> dict:
  response = (
    _db()
    .table("products")
    .insert(
      {
        "name": name.strip(),
        "description": description.strip(),
        "price": price,
        "quantity": quantity,
        "image_url": image_url,
        "image_urls": image_urls or [],
        "category": category,
        "sizes": sizes or [],
        "colors": colors or [],
      }
    )
    .execute()
  )
  product = _one(response.data)
  if not product:
    raise RuntimeError("Mahsulot qo'shilmadi.")
  if quantity > 0:
    _db().table("transactions").insert(
      {
        "product_id": product["id"],
        "type": "kirim",
        "quantity": quantity,
        "admin_id": admin_id,
        "comment": "Boshlang'ich qoldiq",
      }
    ).execute()
  return product


def update_product_price(product_id: int, price: int) -> dict | None:
  response = (
    _db()
    .table("products")
    .update({"price": price})
    .eq("id", product_id)
    .execute()
  )
  return _one(response.data)


def update_product(product_id: int, updates: dict) -> dict | None:
  if not updates:
    return get_product(product_id)
  response = (
    _db()
    .table("products")
    .update(updates)
    .eq("id", product_id)
    .execute()
  )
  return _one(response.data)


def set_product_active(product_id: int, is_active: bool) -> bool:
  response = (
    _db()
    .table("products")
    .update({"is_active": is_active})
    .eq("id", product_id)
    .execute()
  )
  return bool(response.data)


def delete_product(product_id: int) -> bool:
  product = get_product(product_id)
  if not product:
    return False
  try:
    response = (
      _db().table("products").delete().eq("id", product_id).execute()
    )
  except Exception:
    return False

  deleted = bool(response.data)
  image_url = product.get("image_url")
  if deleted and image_url and not str(image_url).startswith("http"):
    image = IMAGES_DIR / image_url
    if image.is_file():
      image.unlink()
  return deleted


def stock_in(
  product_id: int,
  quantity: int,
  admin_id: int,
  comment: str | None = None,
) -> dict | None:
  if quantity <= 0:
    return None
  response = _db().rpc(
    "shop_stock_in",
    {
      "p_product_id": product_id,
      "p_quantity": quantity,
      "p_admin_id": admin_id,
      "p_comment": comment,
    },
  ).execute()
  return _one(response.data)


def write_off(
  product_id: int,
  quantity: int,
  admin_id: int,
  comment: str | None = None,
) -> dict | None:
  if quantity <= 0:
    return None
  response = _db().rpc(
    "shop_write_off",
    {
      "p_product_id": product_id,
      "p_quantity": quantity,
      "p_admin_id": admin_id,
      "p_comment": comment,
    },
  ).execute()
  result = _one(response.data)
  return result if result and result.get("ok", True) else None


# ── Cart (bot jarayoni davomida xotirada saqlanadi) ───────


def get_cart(user_id: int) -> dict[int, int]:
  return _carts.setdefault(user_id, {})


def clear_cart(user_id: int) -> None:
  _carts.pop(user_id, None)


def add_to_cart(user_id: int, product_id: int, quantity: int) -> dict[int, int]:
  cart = get_cart(user_id)
  cart[product_id] = cart.get(product_id, 0) + quantity
  return cart


def cart_details(user_id: int) -> tuple[list[dict], int]:
  cart = get_cart(user_id)
  items: list[dict] = []
  total = 0
  for product_id, qty in list(cart.items()):
    product = get_product(product_id)
    if not product or not product["is_active"] or product["quantity"] <= 0:
      cart.pop(product_id, None)
      continue
    line_qty = min(qty, product["quantity"])
    if line_qty != qty:
      cart[product_id] = line_qty
    line_total = product["price"] * line_qty
    total += line_total
    items.append(
      {
        "product": product,
        "quantity": line_qty,
        "line_total": line_total,
      }
    )
  return items, total


# ── Orders ─────────────────────────────────────────────────


def create_order(
  user_id: int,
  user_name: str | None,
  phone_number: str,
  items: list[dict],
  comment: str = "",
) -> dict | None:
  if not items:
    return None
  response = _db().rpc(
    "shop_create_order",
    {
      "p_user_id": user_id,
      "p_user_name": user_name,
      "p_phone_number": phone_number,
      "p_items": [
        {
          "product_id": item["product_id"],
          "quantity": item["quantity"],
          "size": item.get("size"),
          "color": item.get("color"),
        }
        for item in items
      ],
      "p_comment": comment,
    },
  ).execute()
  result = _one(response.data)
  return result if result and result.get("ok", True) else None


def get_user_orders(user_id: int, limit: int = 20) -> list[dict]:
  response = (
    _db()
    .table("orders")
    .select(ORDER_FIELDS)
    .eq("user_id", user_id)
    .order("created_at", desc=True)
    .limit(limit)
    .execute()
  )
  return response.data or []


def get_orders_by_status(status: str = "pending", limit: int = 30) -> list[dict]:
  response = (
    _db()
    .table("orders")
    .select(ORDER_FIELDS)
    .eq("status", status)
    .order("created_at")
    .limit(limit)
    .execute()
  )
  return response.data or []


def get_order(order_id: int) -> dict | None:
  response = (
    _db()
    .table("orders")
    .select(ORDER_FIELDS)
    .eq("id", order_id)
    .limit(1)
    .execute()
  )
  return _one(response.data)


def get_order_items(order_id: int) -> list[dict]:
  response = (
    _db()
    .table("order_items")
    .select(
      "id,order_id,product_id,quantity,unit_price,size,color,products(name)"
    )
    .eq("order_id", order_id)
    .order("id")
    .execute()
  )
  rows = response.data or []
  for row in rows:
    related = row.pop("products", None) or {}
    if isinstance(related, list):
      related = related[0] if related else {}
    row["product_name"] = related.get("name", "Noma'lum")
  return rows


def approve_order(order_id: int, admin_id: int) -> tuple[bool, str]:
  response = _db().rpc(
    "shop_approve_order",
    {"p_order_id": order_id, "p_admin_id": admin_id},
  ).execute()
  result = _one(response.data) or {}
  return bool(result.get("ok")), result.get("message", "Noma'lum xatolik.")


def reject_order(order_id: int) -> tuple[bool, str]:
  response = _db().rpc(
    "shop_reject_order",
    {"p_order_id": order_id},
  ).execute()
  result = _one(response.data) or {}
  return bool(result.get("ok")), result.get("message", "Noma'lum xatolik.")


# ── Stats ──────────────────────────────────────────────────


def get_stats() -> dict:
  products = (
    _db().table("products").select("price,quantity,is_active").execute().data
    or []
  )
  orders = (
    _db().table("orders").select("status,total_price").execute().data or []
  )
  transactions = (
    _db()
    .table("transactions")
    .select("id,product_id,type,quantity,comment,created_at")
    .order("created_at", desc=True)
    .limit(500)
    .execute()
    .data
    or []
  )

  recent = transactions[:15]
  product_ids = {row["product_id"] for row in recent}
  names: dict[int, str] = {}
  if product_ids:
    product_rows = (
      _db()
      .table("products")
      .select("id,name")
      .in_("id", list(product_ids))
      .execute()
      .data
      or []
    )
    names = {row["id"]: row["name"] for row in product_rows}
  for row in recent:
    row["product_name"] = names.get(row["product_id"], "Noma'lum")

  active = [row for row in products if row["is_active"]]
  return {
    "active_products": len(active),
    "total_stock": sum(row["quantity"] for row in active),
    "stock_value": sum(row["price"] * row["quantity"] for row in active),
    "pending_orders": sum(row["status"] == "pending" for row in orders),
    "approved_orders": sum(row["status"] == "approved" for row in orders),
    "rejected_orders": sum(row["status"] == "rejected" for row in orders),
    "revenue": sum(
      row["total_price"] for row in orders if row["status"] == "approved"
    ),
    "sold_units": sum(
      row["quantity"] for row in transactions if row["type"] == "sotuv"
    ),
    "recent": recent,
  }
