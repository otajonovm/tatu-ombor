from pathlib import Path
from typing import Any
import json
import logging
import uuid

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

IMAGES_DIR = Path(__file__).parent / "images"
CARTS_FILE = Path(__file__).parent / "data" / "carts.json"
PRODUCT_FIELDS = (
  "id,name,description,price,quantity,image_url,image_urls,category,"
  "sizes,colors,is_active,created_at"
)
LEGACY_PRODUCT_FIELDS = (
  "id,name,description,price,quantity,image_url,is_active,created_at"
)
ORDER_FIELDS = (
  "id,user_id,user_name,phone_number,comment,total_price,status,created_at"
)
LEGACY_ORDER_FIELDS = (
  "id,user_id,user_name,phone_number,total_price,status,created_at"
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


def _normalise_product(product: dict) -> dict:
  """Eski products jadvali bilan TMA o'tish davrida ham ishlaydi."""
  product.setdefault("image_urls", [])
  if not product["image_urls"] and product.get("image_url"):
    product["image_urls"] = [product["image_url"]]
  product.setdefault("category", "suvenir")
  product.setdefault("sizes", [])
  product.setdefault("colors", [])
  return product


def _normalise_products(products: list[dict]) -> list[dict]:
  return [_normalise_product(product) for product in products]


def _normalise_order(order: dict) -> dict:
  order.setdefault("comment", "")
  return order


def _normalise_orders(orders: list[dict]) -> list[dict]:
  return [_normalise_order(order) for order in orders]


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
        "To'liq seed yozuvi muvaffaqiyatsiz (%s). Legacy ustunlar bilan urinilmoqda.",
        error,
      )
      legacy_rows = [
        {
          "name": row["name"],
          "description": row["description"],
          "price": row["price"],
          "quantity": row["quantity"],
          "image_url": row["image_url"],
        }
        for row in missing
      ]
      try:
        _db().table("products").insert(legacy_rows).execute()
      except Exception as legacy_error:
        logger.warning(
          "Supabase yozishni blokladi: %s. Yangilangan "
          "supabase/schema.sql faylini SQL Editor'da ishga tushiring.",
          legacy_error,
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
  try:
    response = (
      _db()
      .table("products")
      .select(PRODUCT_FIELDS)
      .eq("is_active", True)
      .gt("quantity", 0)
      .order("name")
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("products")
      .select(LEGACY_PRODUCT_FIELDS)
      .eq("is_active", True)
      .gt("quantity", 0)
      .order("name")
      .execute()
    )
  return _normalise_products(response.data or [])


def get_all_products(include_inactive: bool = True) -> list[dict]:
  try:
    query = _db().table("products").select(PRODUCT_FIELDS)
    if not include_inactive:
      query = query.eq("is_active", True)
    response = query.order("name").execute()
  except Exception:
    query = _db().table("products").select(LEGACY_PRODUCT_FIELDS)
    if not include_inactive:
      query = query.eq("is_active", True)
    response = query.order("name").execute()
  rows = _normalise_products(response.data or [])
  return sorted(rows, key=lambda row: (not row["is_active"], row["name"]))


def get_product(product_id: int) -> dict | None:
  try:
    response = (
      _db()
      .table("products")
      .select(PRODUCT_FIELDS)
      .eq("id", product_id)
      .limit(1)
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("products")
      .select(LEGACY_PRODUCT_FIELDS)
      .eq("id", product_id)
      .limit(1)
      .execute()
    )
  product = _one(response.data)
  return _normalise_product(product) if product else None


def get_product_by_name(name: str) -> dict | None:
  try:
    response = (
      _db()
      .table("products")
      .select(PRODUCT_FIELDS)
      .eq("name", name.strip())
      .limit(1)
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("products")
      .select(LEGACY_PRODUCT_FIELDS)
      .eq("name", name.strip())
      .limit(1)
      .execute()
    )
  product = _one(response.data)
  return _normalise_product(product) if product else None


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
  base_row = {
    "name": name.strip(),
    "description": description.strip(),
    "price": price,
    "quantity": quantity,
    "image_url": image_url,
  }
  full_row = {
    **base_row,
    "image_urls": image_urls or ([image_url] if image_url else []),
    "category": category,
    "sizes": sizes or [],
    "colors": colors or [],
  }
  try:
    response = _db().table("products").insert(full_row).execute()
  except Exception as error:
    # Eski products jadvalida category/image_urls/sizes/colors yo'q bo'lishi mumkin.
    logger.warning(
      "To'liq mahsulot yozuvi muvaffaqiyatsiz (%s). Legacy ustunlar bilan urinilmoqda.",
      error,
    )
    response = _db().table("products").insert(base_row).execute()

  product = _one(response.data)
  if not product:
    raise RuntimeError("Mahsulot qo'shilmadi.")
  product = _normalise_product(product)
  if quantity > 0:
    try:
      _db().table("transactions").insert(
        {
          "product_id": product["id"],
          "type": "kirim",
          "quantity": quantity,
          "admin_id": admin_id,
          "comment": "Boshlang'ich qoldiq",
        }
      ).execute()
    except Exception as error:
      logger.warning("Boshlang'ich kirim yozilmadi: %s", error)
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


# ── Cart (diskka saqlanadi — bot qayta ishga tushsa ham qoladi) ──


def _load_carts() -> None:
  global _carts
  if _carts:
    return
  if not CARTS_FILE.is_file():
    return
  try:
    raw = json.loads(CARTS_FILE.read_text(encoding="utf-8"))
    _carts = {
      int(uid): {int(pid): int(qty) for pid, qty in items.items()}
      for uid, items in raw.items()
    }
  except Exception as error:
    logger.warning("Savat fayli o'qilmadi: %s", error)


def _save_carts() -> None:
  try:
    CARTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
      str(uid): {str(pid): qty for pid, qty in items.items()}
      for uid, items in _carts.items()
      if items
    }
    CARTS_FILE.write_text(
      json.dumps(payload, ensure_ascii=False),
      encoding="utf-8",
    )
  except Exception as error:
    logger.warning("Savat fayli yozilmadi: %s", error)


def get_cart(user_id: int) -> dict[int, int]:
  _load_carts()
  return _carts.setdefault(user_id, {})


def clear_cart(user_id: int) -> None:
  _load_carts()
  _carts.pop(user_id, None)
  _save_carts()


def add_to_cart(user_id: int, product_id: int, quantity: int) -> dict[int, int]:
  cart = get_cart(user_id)
  cart[product_id] = cart.get(product_id, 0) + quantity
  _save_carts()
  return cart


def cart_details(user_id: int) -> tuple[list[dict], int]:
  cart = get_cart(user_id)
  items: list[dict] = []
  total = 0
  changed = False
  for product_id, qty in list(cart.items()):
    product = get_product(product_id)
    if not product or not product["is_active"] or product["quantity"] <= 0:
      cart.pop(product_id, None)
      changed = True
      continue
    line_qty = min(qty, product["quantity"])
    if line_qty != qty:
      cart[product_id] = line_qty
      changed = True
    line_total = product["price"] * line_qty
    total += line_total
    items.append(
      {
        "product": product,
        "quantity": line_qty,
        "line_total": line_total,
      }
    )
  if changed:
    _save_carts()
  return items, total


# ── Orders ─────────────────────────────────────────────────


def _create_order_direct(
  user_id: int,
  user_name: str | None,
  phone_number: str,
  items: list[dict],
  comment: str = "",
) -> dict | None:
  """RPC yo'q yoki eski sxema bo'lsa — to'g'ridan-to'g'ri insert."""
  prepared: list[dict] = []
  total = 0
  for item in items:
    product = get_product(int(item["product_id"]))
    qty = int(item["quantity"])
    if (
      not product
      or not product.get("is_active", True)
      or qty <= 0
      or int(product["quantity"]) < qty
    ):
      return None
    prepared.append(
      {
        "product_id": product["id"],
        "quantity": qty,
        "unit_price": int(product["price"]),
        "size": item.get("size") or None,
        "color": item.get("color") or None,
      }
    )
    total += int(product["price"]) * qty

  order_row = {
    "user_id": user_id,
    "user_name": user_name,
    "phone_number": phone_number,
    "total_price": total,
    "status": "pending",
  }
  try:
    response = (
      _db()
      .table("orders")
      .insert({**order_row, "comment": comment or ""})
      .execute()
    )
  except Exception:
    response = _db().table("orders").insert(order_row).execute()

  order = _one(response.data)
  if not order:
    return None

  for line in prepared:
    full_item = {
      "order_id": order["id"],
      "product_id": line["product_id"],
      "quantity": line["quantity"],
      "unit_price": line["unit_price"],
      "size": line["size"],
      "color": line["color"],
    }
    try:
      _db().table("order_items").insert(full_item).execute()
    except Exception:
      _db().table("order_items").insert(
        {
          "order_id": order["id"],
          "product_id": line["product_id"],
          "quantity": line["quantity"],
          "unit_price": line["unit_price"],
        }
      ).execute()

  return _normalise_order(order)


def create_order(
  user_id: int,
  user_name: str | None,
  phone_number: str,
  items: list[dict],
  comment: str = "",
) -> dict | None:
  if not items:
    return None

  # Avvalo to'g'ridan-to'g'ri insert — bir nechta mahsulotli buyurtma ishonchli.
  try:
    direct = _create_order_direct(
      user_id, user_name, phone_number, items, comment
    )
    if direct:
      return direct
  except Exception as error:
    logger.warning("Direct create_order xato: %s", error)

  rpc_items = [
    {
      "product_id": int(item["product_id"]),
      "quantity": int(item["quantity"]),
      "size": item.get("size"),
      "color": item.get("color"),
    }
    for item in items
  ]
  base_params = {
    "p_user_id": user_id,
    "p_user_name": user_name,
    "p_phone_number": phone_number,
    "p_items": rpc_items,
  }

  try:
    response = _db().rpc(
      "shop_create_order",
      {**base_params, "p_comment": comment},
    ).execute()
  except Exception:
    try:
      response = _db().rpc("shop_create_order", base_params).execute()
    except Exception as legacy_error:
      logger.warning("shop_create_order muvaffaqiyatsiz: %s", legacy_error)
      return None

  result = _one(response.data)
  if not isinstance(result, dict):
    return None
  if result.get("ok") is False:
    return None
  if "id" in result:
    return _normalise_order(result)
  nested = result.get("order")
  if isinstance(nested, dict) and "id" in nested:
    return _normalise_order(nested)
  return None


def get_user_orders(user_id: int, limit: int = 20) -> list[dict]:
  try:
    response = (
      _db()
      .table("orders")
      .select(ORDER_FIELDS)
      .eq("user_id", user_id)
      .order("created_at", desc=True)
      .limit(limit)
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("orders")
      .select(LEGACY_ORDER_FIELDS)
      .eq("user_id", user_id)
      .order("created_at", desc=True)
      .limit(limit)
      .execute()
    )
  return _normalise_orders(response.data or [])


def get_orders_by_status(status: str = "pending", limit: int = 30) -> list[dict]:
  try:
    response = (
      _db()
      .table("orders")
      .select(ORDER_FIELDS)
      .eq("status", status)
      .order("created_at")
      .limit(limit)
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("orders")
      .select(LEGACY_ORDER_FIELDS)
      .eq("status", status)
      .order("created_at")
      .limit(limit)
      .execute()
    )
  return _normalise_orders(response.data or [])


def get_order(order_id: int) -> dict | None:
  try:
    response = (
      _db()
      .table("orders")
      .select(ORDER_FIELDS)
      .eq("id", order_id)
      .limit(1)
      .execute()
    )
  except Exception:
    response = (
      _db()
      .table("orders")
      .select(LEGACY_ORDER_FIELDS)
      .eq("id", order_id)
      .limit(1)
      .execute()
    )
  order = _one(response.data)
  return _normalise_order(order) if order else None


def get_order_items(order_id: int) -> list[dict]:
  try:
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
  except Exception:
    response = (
      _db()
      .table("order_items")
      .select("id,order_id,product_id,quantity,unit_price,products(name)")
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
    row.setdefault("size", None)
    row.setdefault("color", None)
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


# ── Payments (Telegram / Click) ─────────────────────────────


def som_to_tiyin(amount_som: int) -> int:
  """Telegram Payments UZS: 1 so'm = 100 tiyin."""
  return max(0, int(amount_som)) * 100


def tiyin_to_som(amount_tiyin: int) -> int:
  return int(amount_tiyin) // 100


def parse_order_payload(payload: str) -> int | None:
  if not payload or not payload.startswith("order_"):
    return None
  raw = payload.removeprefix("order_").strip()
  if not raw.isdigit():
    return None
  return int(raw)


def validate_order_for_payment(order_id: int) -> tuple[bool, str]:
  """Pre-checkout: buyurtma pending va barcha mahsulotlar faol/qoldiq yetarli."""
  order = get_order(order_id)
  if not order:
    return False, "Buyurtma topilmadi."
  if order["status"] == "paid":
    return False, "Buyurtma allaqachon to'langan."
  if order["status"] != "pending":
    return False, "Bu buyurtma uchun to'lov qabul qilinmaydi."
  if int(order.get("total_price") or 0) <= 0:
    return False, "Buyurtma summasi noto'g'ri."

  items = get_order_items(order_id)
  if not items:
    return False, "Buyurtmada mahsulot yo'q."

  for item in items:
    product = get_product(int(item["product_id"]))
    name = item.get("product_name") or (product or {}).get("name") or "Mahsulot"
    qty = int(item["quantity"])
    if not product or not product.get("is_active", True):
      return False, f"«{name}» sotuvda emas."
    if int(product["quantity"]) < qty:
      return False, (
        f"«{name}» uchun qoldiq yetarli emas "
        f"({product['quantity']}/{qty})."
      )
  return True, "OK"


def _mark_order_paid_direct(
  order_id: int,
  payment_charge_id: str | None = None,
) -> tuple[bool, str]:
  """RPC yo'q bo'lsa — stock/transaction/status ni ketma-ket yangilaydi."""
  ok, message = validate_order_for_payment(order_id)
  if not ok:
    # Idempotent: allaqachon paid
    order = get_order(order_id)
    if order and order["status"] == "paid":
      return True, "Buyurtma allaqachon to'langan."
    return False, message

  items = get_order_items(order_id)
  for item in items:
    product_id = int(item["product_id"])
    qty = int(item["quantity"])
    product = get_product(product_id)
    if not product:
      return False, "Mahsulot topilmadi."
    new_qty = int(product["quantity"]) - qty
    if new_qty < 0:
      return False, "Qoldiq yetarli emas."
    _db().table("products").update({"quantity": new_qty}).eq(
      "id", product_id
    ).execute()
    _db().table("transactions").insert(
      {
        "product_id": product_id,
        "type": "sotuv",
        "quantity": qty,
        "admin_id": None,
        "comment": f"Click to'lov · buyurtma #{order_id}",
      }
    ).execute()

  updates: dict[str, Any] = {"status": "paid"}
  if payment_charge_id:
    updates["payment_charge_id"] = payment_charge_id
  try:
    _db().table("orders").update(updates).eq("id", order_id).execute()
  except Exception as error:
    # Eski CHECK constraint (paid yo'q) — approved ga tushamiz.
    logger.warning(
      "status=paid yozilmadi (%s). approved + schema yangilang.", error
    )
    fallback = {"status": "approved"}
    if payment_charge_id:
      try:
        _db().table("orders").update(
          {**fallback, "payment_charge_id": payment_charge_id}
        ).eq("id", order_id).execute()
      except Exception:
        _db().table("orders").update(fallback).eq("id", order_id).execute()
    else:
      _db().table("orders").update(fallback).eq("id", order_id).execute()

  return True, "To'lov qabul qilindi."


def mark_order_paid(
  order_id: int,
  payment_charge_id: str | None = None,
) -> tuple[bool, str]:
  try:
    response = _db().rpc(
      "shop_mark_order_paid",
      {
        "p_order_id": order_id,
        "p_payment_charge_id": payment_charge_id,
      },
    ).execute()
    result = _one(response.data) or {}
    if "ok" in result:
      return bool(result.get("ok")), result.get(
        "message", "Noma'lum xatolik."
      )
  except Exception as error:
    logger.warning("shop_mark_order_paid RPC ishlamadi: %s", error)

  return _mark_order_paid_direct(order_id, payment_charge_id)


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
    "paid_orders": sum(row["status"] == "paid" for row in orders),
    "approved_orders": sum(row["status"] == "approved" for row in orders),
    "rejected_orders": sum(row["status"] == "rejected" for row in orders),
    "revenue": sum(
      row["total_price"]
      for row in orders
      if row["status"] in {"approved", "paid"}
    ),
    "sold_units": sum(
      row["quantity"] for row in transactions if row["type"] == "sotuv"
    ),
    "recent": recent,
  }
