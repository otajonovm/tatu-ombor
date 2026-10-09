-- TATU Brend Do'koni — mavjud bazaga yangilash
-- Supabase → SQL Editor → New query → shu faylni TO'LIQ yopishtiring → Run
-- Ma'lumotlarni o'chirmaydi. Qayta ishga tushirish xavfsiz.

-- ── Ustunlar ──────────────────────────────────────────────

ALTER TABLE products ADD COLUMN IF NOT EXISTS image_urls JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE products ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'suvenir';
ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE orders ADD COLUMN IF NOT EXISTS comment TEXT NOT NULL DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_charge_id TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS stock_reserved BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE order_items ADD COLUMN IF NOT EXISTS size TEXT;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS color TEXT;

DO $$
BEGIN
  ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;
  ALTER TABLE orders
    ADD CONSTRAINT orders_status_check
    CHECK (status IN ('pending', 'paid', 'approved', 'rejected'));
EXCEPTION
  WHEN others THEN
    NULL;
END $$;

-- ── Tugagan mahsulotlarni arxivlash ───────────────────────

UPDATE products
SET is_active = FALSE
WHERE quantity <= 0 AND is_active = TRUE;

CREATE OR REPLACE FUNCTION shop_archive_if_empty()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.quantity <= 0 THEN
    NEW.quantity := 0;
    NEW.is_active := FALSE;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_products_archive_if_empty ON products;
CREATE TRIGGER trg_products_archive_if_empty
BEFORE INSERT OR UPDATE OF quantity ON products
FOR EACH ROW
EXECUTE PROCEDURE shop_archive_if_empty();

-- ── Kirim: arxivdagi mahsulotga ham ishlaydi ──────────────

CREATE OR REPLACE FUNCTION shop_stock_in(
  p_product_id INTEGER,
  p_quantity INTEGER,
  p_admin_id BIGINT,
  p_comment TEXT DEFAULT NULL
)
RETURNS SETOF products
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF p_quantity <= 0 THEN
    RETURN;
  END IF;

  INSERT INTO transactions (product_id, type, quantity, admin_id, comment)
  SELECT id, 'kirim', p_quantity, p_admin_id, p_comment
  FROM products
  WHERE id = p_product_id;

  IF NOT FOUND THEN
    RETURN;
  END IF;

  RETURN QUERY
  UPDATE products
  SET quantity = quantity + p_quantity,
      is_active = TRUE
  WHERE id = p_product_id
  RETURNING *;
END;
$$;

CREATE OR REPLACE FUNCTION shop_write_off(
  p_product_id INTEGER,
  p_quantity INTEGER,
  p_admin_id BIGINT,
  p_comment TEXT DEFAULT NULL
)
RETURNS SETOF products
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF p_quantity <= 0 THEN
    RETURN;
  END IF;

  RETURN QUERY
  UPDATE products
  SET quantity = quantity - p_quantity,
      is_active = (quantity - p_quantity > 0)
  WHERE id = p_product_id AND quantity >= p_quantity
  RETURNING *;

  IF FOUND THEN
    INSERT INTO transactions (product_id, type, quantity, admin_id, comment)
    VALUES (
      p_product_id, 'hisobdan_chiqarish', p_quantity, p_admin_id, p_comment
    );
  END IF;
END;
$$;

GRANT EXECUTE ON FUNCTION shop_stock_in(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_write_off(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;
