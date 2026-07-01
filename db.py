import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "ombor.db"


@contextmanager
def get_connection():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  try:
    yield conn
    conn.commit()
  finally:
    conn.close()


def _migrate_schema(conn: sqlite3.Connection) -> None:
  columns = {
    row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()
  }
  if "recipient_name" not in columns:
    conn.execute("ALTER TABLE transactions ADD COLUMN recipient_name TEXT")
  columns = {
    row[1] for row in conn.execute("PRAGMA table_info(products)").fetchall()
  }
  if "image_path" not in columns:
    conn.execute("ALTER TABLE products ADD COLUMN image_path TEXT")


def init_db(default_products: list[dict]) -> None:
  with get_connection() as conn:
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        quantity INTEGER NOT NULL DEFAULT 0,
        image_path TEXT
      )
      """
    )
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        user_name TEXT,
        action TEXT NOT NULL,
        amount INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id)
      )
      """
    )
    _migrate_schema(conn)

    for product in default_products:
      image = product.get("image")
      conn.execute(
        """
        INSERT OR IGNORE INTO products (name, quantity, image_path)
        VALUES (?, ?, ?)
        """,
        (product["name"], product["quantity"], image),
      )
      if image:
        conn.execute(
          """
          UPDATE products
          SET image_path = ?
          WHERE name = ? AND (image_path IS NULL OR image_path = '')
          """,
          (image, product["name"]),
        )


def get_all_products() -> list[dict]:
  with get_connection() as conn:
    rows = conn.execute(
      "SELECT id, name, quantity, image_path FROM products ORDER BY name"
    ).fetchall()
  return [dict(row) for row in rows]


def get_product(product_id: int) -> dict | None:
  with get_connection() as conn:
    row = conn.execute(
      "SELECT id, name, quantity, image_path FROM products WHERE id = ?",
      (product_id,),
    ).fetchone()
  return dict(row) if row else None


def update_quantity(
  product_id: int,
  delta: int,
  user_id: int,
  user_name: str,
  action: str,
  recipient_name: str | None = None,
) -> dict | None:
  with get_connection() as conn:
    row = conn.execute(
      "SELECT id, name, quantity, image_path FROM products WHERE id = ?",
      (product_id,),
    ).fetchone()
    if not row:
      return None

    new_qty = row["quantity"] + delta
    if new_qty < 0:
      return None

    conn.execute(
      "UPDATE products SET quantity = ? WHERE id = ?",
      (new_qty, product_id),
    )
    conn.execute(
      """
      INSERT INTO transactions (
        product_id, user_id, user_name, action, amount, created_at, recipient_name
      )
      VALUES (?, ?, ?, ?, ?, ?, ?)
      """,
      (
        product_id,
        user_id,
        user_name,
        action,
        abs(delta),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        recipient_name,
      ),
    )
    return {
      "id": row["id"],
      "name": row["name"],
      "quantity": new_qty,
      "image_path": row["image_path"],
    }


def cleanup_bad_products(default_names: set[str]) -> int:
  """Rasmsiz va noto'g'ri qo'shilgan mahsulotlarni o'chiradi."""
  removed = 0
  with get_connection() as conn:
    rows = conn.execute(
      "SELECT id, name, image_path FROM products"
    ).fetchall()
    for row in rows:
      name = row["name"]
      has_image = bool(row["image_path"])
      is_default = name in default_names
      if not has_image and not is_default:
        conn.execute("DELETE FROM products WHERE id = ?", (row["id"],))
        removed += 1
      elif name.isdigit():
        conn.execute("DELETE FROM products WHERE id = ?", (row["id"],))
        removed += 1
  return removed


def fix_wrong_kirim(product_name: str, wrong_qty: int) -> bool:
  """Noto'g'ri kirim qilingan mahsulot qoldig'ini tuzatadi."""
  with get_connection() as conn:
    row = conn.execute(
      "SELECT id, quantity FROM products WHERE name = ?",
      (product_name,),
    ).fetchone()
    if not row or row["quantity"] != wrong_qty:
      return False
    conn.execute(
      "UPDATE products SET quantity = 0 WHERE id = ?",
      (row["id"],),
    )
  return True


def get_product_by_name(name: str) -> dict | None:
  with get_connection() as conn:
    row = conn.execute(
      "SELECT id, name, quantity, image_path FROM products WHERE name = ?",
      (name.strip(),),
    ).fetchone()
  return dict(row) if row else None


def add_product(name: str, quantity: int = 0, image_path: str | None = None) -> dict:
  with get_connection() as conn:
    conn.execute(
      "INSERT INTO products (name, quantity, image_path) VALUES (?, ?, ?)",
      (name.strip(), quantity, image_path),
    )
    row = conn.execute(
      "SELECT id, name, quantity, image_path FROM products WHERE name = ?",
      (name.strip(),),
    ).fetchone()
  return dict(row)


def delete_product(product_id: int) -> bool:
  image_path = None
  deleted = False

  with get_connection() as conn:
    row = conn.execute(
      "SELECT image_path FROM products WHERE id = ?",
      (product_id,),
    ).fetchone()
    cursor = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    deleted = cursor.rowcount > 0
    if row:
      image_path = row["image_path"]

  if deleted and image_path:
    image = Path(__file__).parent / "images" / image_path
    if image.is_file():
      image.unlink()

  return deleted


def get_recent_transactions(limit: int = 10) -> list[dict]:
  with get_connection() as conn:
    rows = conn.execute(
      """
      SELECT t.id, p.name AS product_name, t.user_name, t.action,
             t.amount, t.created_at, t.recipient_name
      FROM transactions t
      JOIN products p ON p.id = t.product_id
      ORDER BY t.id DESC
      LIMIT ?
      """,
      (limit,),
    ).fetchall()
  return [dict(row) for row in rows]
