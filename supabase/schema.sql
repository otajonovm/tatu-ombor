-- TATU Brend Do'koni — Supabase SQL Editor
-- Bu migratsiya mavjud ma'lumotlarni o'chirmaydi.
-- Supabase SQL Editor'da to'liq skriptni ishga tushiring.

CREATE TABLE IF NOT EXISTS products (
  id          SERIAL PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL DEFAULT '',
  price       INTEGER NOT NULL DEFAULT 0 CHECK (price >= 0),
  quantity    INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
  image_url   TEXT,
  image_urls  JSONB NOT NULL DEFAULT '[]'::jsonb,
  category    TEXT NOT NULL DEFAULT 'suvenir',
  sizes       JSONB NOT NULL DEFAULT '[]'::jsonb,
  colors      JSONB NOT NULL DEFAULT '[]'::jsonb,
  is_active   BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id           SERIAL PRIMARY KEY,
  user_id      BIGINT NOT NULL,
  user_name    TEXT,
  phone_number TEXT NOT NULL,
  comment      TEXT NOT NULL DEFAULT '',
  total_price  INTEGER NOT NULL DEFAULT 0 CHECK (total_price >= 0),
  status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'paid', 'approved', 'rejected')),
  payment_charge_id TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
  id          SERIAL PRIMARY KEY,
  order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id  INTEGER NOT NULL REFERENCES products(id),
  quantity    INTEGER NOT NULL CHECK (quantity > 0),
  unit_price  INTEGER NOT NULL CHECK (unit_price >= 0),
  size        TEXT,
  color       TEXT
);

CREATE TABLE IF NOT EXISTS transactions (
  id          SERIAL PRIMARY KEY,
  product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  type        TEXT NOT NULL
                CHECK (type IN ('kirim', 'sotuv', 'hisobdan_chiqarish')),
  quantity    INTEGER NOT NULL CHECK (quantity > 0),
  admin_id    BIGINT,
  comment     TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_transactions_product_id ON transactions(product_id);
CREATE INDEX idx_transactions_created ON transactions(created_at DESC);

ALTER TABLE products ADD COLUMN IF NOT EXISTS image_urls JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE products ADD COLUMN IF NOT EXISTS category TEXT NOT NULL DEFAULT 'suvenir';
ALTER TABLE products ADD COLUMN IF NOT EXISTS sizes JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE products ADD COLUMN IF NOT EXISTS colors JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS comment TEXT NOT NULL DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_charge_id TEXT;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS size TEXT;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS color TEXT;
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

-- Telegram Payments: paid status
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

-- REST API orqali atomik amallar (supabase-py RPC)

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
  WHERE id = p_product_id AND is_active = TRUE;

  RETURN QUERY
  UPDATE products
  SET quantity = quantity + p_quantity
  WHERE id = p_product_id AND is_active = TRUE
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
  SET quantity = quantity - p_quantity
  WHERE id = p_product_id AND quantity >= p_quantity
  RETURNING *;

  IF FOUND THEN
    INSERT INTO transactions (product_id, type, quantity, admin_id, comment)
    VALUES (
      p_product_id,
      'hisobdan_chiqarish',
      p_quantity,
      p_admin_id,
      p_comment
    );
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION shop_create_order(
  p_user_id BIGINT,
  p_user_name TEXT,
  p_phone_number TEXT,
  p_items JSONB,
  p_comment TEXT DEFAULT ''
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_item RECORD;
  v_product products%ROWTYPE;
  v_order orders%ROWTYPE;
  v_total INTEGER := 0;
BEGIN
  IF p_items IS NULL OR jsonb_array_length(p_items) = 0 THEN
    RETURN jsonb_build_object('ok', FALSE, 'message', 'Savat bo''sh.');
  END IF;

  FOR v_item IN
    SELECT * FROM jsonb_to_recordset(p_items)
      AS x(product_id INTEGER, quantity INTEGER)
  LOOP
    SELECT * INTO v_product
    FROM products
    WHERE id = v_item.product_id AND is_active = TRUE;

    IF NOT FOUND OR v_item.quantity <= 0
       OR v_product.quantity < v_item.quantity THEN
      RETURN jsonb_build_object(
        'ok', FALSE,
        'message', 'Mahsulot qoldig''i yetarli emas.'
      );
    END IF;

    v_total := v_total + (v_product.price * v_item.quantity);
  END LOOP;

  INSERT INTO orders (
    user_id, user_name, phone_number, comment, total_price, status
  )
  VALUES (
    p_user_id, p_user_name, p_phone_number, COALESCE(p_comment, ''),
    v_total, 'pending'
  )
  RETURNING * INTO v_order;

  FOR v_item IN
    SELECT * FROM jsonb_to_recordset(p_items)
      AS x(product_id INTEGER, quantity INTEGER, size TEXT, color TEXT)
  LOOP
    SELECT * INTO v_product FROM products WHERE id = v_item.product_id;
    INSERT INTO order_items (
      order_id, product_id, quantity, unit_price, size, color
    )
    VALUES (
      v_order.id, v_item.product_id, v_item.quantity, v_product.price,
      v_item.size, v_item.color
    );
  END LOOP;

  RETURN to_jsonb(v_order);
END;
$$;

CREATE OR REPLACE FUNCTION shop_approve_order(
  p_order_id INTEGER,
  p_admin_id BIGINT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_order orders%ROWTYPE;
  v_item RECORD;
  v_product products%ROWTYPE;
BEGIN
  SELECT * INTO v_order
  FROM orders
  WHERE id = p_order_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('ok', FALSE, 'message', 'Buyurtma topilmadi.');
  END IF;
  IF v_order.status <> 'pending' THEN
    RETURN jsonb_build_object(
      'ok', FALSE,
      'message', 'Buyurtma allaqachon ko''rib chiqilgan.'
    );
  END IF;

  FOR v_item IN
    SELECT oi.product_id, oi.quantity, p.name
    FROM order_items oi
    JOIN products p ON p.id = oi.product_id
    WHERE oi.order_id = p_order_id
  LOOP
    SELECT * INTO v_product
    FROM products
    WHERE id = v_item.product_id
    FOR UPDATE;

    IF v_product.quantity < v_item.quantity THEN
      RETURN jsonb_build_object(
        'ok', FALSE,
        'message', format(
          '«%s» uchun qoldiq yetarli emas (%s/%s).',
          v_item.name, v_product.quantity, v_item.quantity
        )
      );
    END IF;
  END LOOP;

  FOR v_item IN
    SELECT product_id, quantity
    FROM order_items
    WHERE order_id = p_order_id
  LOOP
    UPDATE products
    SET quantity = quantity - v_item.quantity
    WHERE id = v_item.product_id;

    INSERT INTO transactions (
      product_id, type, quantity, admin_id, comment
    )
    VALUES (
      v_item.product_id,
      'sotuv',
      v_item.quantity,
      p_admin_id,
      format('Buyurtma #%s', p_order_id)
    );
  END LOOP;

  UPDATE orders SET status = 'approved' WHERE id = p_order_id;
  RETURN jsonb_build_object(
    'ok', TRUE,
    'message', 'Buyurtma qabul qilindi.'
  );
END;
$$;

CREATE OR REPLACE FUNCTION shop_reject_order(p_order_id INTEGER)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_status TEXT;
BEGIN
  SELECT status INTO v_status
  FROM orders
  WHERE id = p_order_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('ok', FALSE, 'message', 'Buyurtma topilmadi.');
  END IF;
  IF v_status <> 'pending' THEN
    RETURN jsonb_build_object(
      'ok', FALSE,
      'message', 'Buyurtma allaqachon ko''rib chiqilgan.'
    );
  END IF;

  UPDATE orders SET status = 'rejected' WHERE id = p_order_id;
  RETURN jsonb_build_object(
    'ok', TRUE,
    'message', 'Buyurtma bekor qilindi.'
  );
END;
$$;

DROP FUNCTION IF EXISTS shop_mark_order_paid(INTEGER, TEXT);

-- Telegram Payments muvaffaqiyatli to'lov: status=paid + ombor kamaytirish
CREATE OR REPLACE FUNCTION shop_mark_order_paid(
  p_order_id INTEGER,
  p_payment_charge_id TEXT DEFAULT NULL,
  p_provider TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_order orders%ROWTYPE;
  v_item RECORD;
  v_provider TEXT;
BEGIN
  v_provider := CASE lower(coalesce(p_provider, ''))
    WHEN 'click' THEN 'Click'
    WHEN 'payme' THEN 'Payme'
    ELSE 'To''lov'
  END;

  SELECT * INTO v_order
  FROM orders
  WHERE id = p_order_id
  FOR UPDATE;

  IF NOT FOUND THEN
    RETURN jsonb_build_object('ok', FALSE, 'message', 'Buyurtma topilmadi.');
  END IF;

  IF v_order.status = 'paid' THEN
    RETURN jsonb_build_object(
      'ok', TRUE,
      'message', 'Buyurtma allaqachon to''langan.',
      'order', to_jsonb(v_order)
    );
  END IF;

  IF v_order.status <> 'pending' THEN
    RETURN jsonb_build_object(
      'ok', FALSE,
      'message', 'Bu buyurtma uchun to''lov qabul qilinmaydi.'
    );
  END IF;

  IF (SELECT COUNT(*) FROM order_items WHERE order_id = p_order_id) = 0 THEN
    RETURN jsonb_build_object(
      'ok', FALSE,
      'message', 'Buyurtmada mahsulot yo''q.'
    );
  END IF;

  IF (
    SELECT COUNT(*) FROM order_items WHERE order_id = p_order_id
  ) <> (
    SELECT COUNT(*)
    FROM order_items oi
    JOIN products p ON p.id = oi.product_id
    WHERE oi.order_id = p_order_id
  ) THEN
    RETURN jsonb_build_object(
      'ok', FALSE,
      'message', 'Kechirasiz, tanlangan mahsulot omborda yetarli emas.'
    );
  END IF;

  FOR v_item IN
    SELECT oi.product_id, oi.quantity, p.is_active, p.quantity AS stock
    FROM order_items oi
    JOIN products p ON p.id = oi.product_id
    WHERE oi.order_id = p_order_id
    FOR UPDATE OF p
  LOOP
    IF v_item.is_active IS NOT TRUE OR v_item.stock < v_item.quantity THEN
      RETURN jsonb_build_object(
        'ok', FALSE,
        'message', 'Kechirasiz, tanlangan mahsulot omborda yetarli emas.'
      );
    END IF;
  END LOOP;

  FOR v_item IN
    SELECT product_id, quantity
    FROM order_items
    WHERE order_id = p_order_id
  LOOP
    UPDATE products
    SET quantity = quantity - v_item.quantity
    WHERE id = v_item.product_id
      AND is_active = TRUE
      AND quantity >= v_item.quantity;

    IF NOT FOUND THEN
      RAISE EXCEPTION 'stock changed during payment';
    END IF;

    INSERT INTO transactions (
      product_id, type, quantity, admin_id, comment
    )
    VALUES (
      v_item.product_id,
      'sotuv',
      v_item.quantity,
      NULL,
      format('%s to''lov · buyurtma #%s', v_provider, p_order_id)
    );
  END LOOP;

  UPDATE orders
  SET
    status = 'paid',
    payment_charge_id = COALESCE(p_payment_charge_id, payment_charge_id)
  WHERE id = p_order_id
  RETURNING * INTO v_order;

  RETURN jsonb_build_object(
    'ok', TRUE,
    'message', 'To''lov qabul qilindi.',
    'order', to_jsonb(v_order)
  );
END;
$$;

GRANT SELECT, INSERT, UPDATE, DELETE
  ON products, orders, order_items, transactions
  TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_stock_in(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_write_off(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_create_order(BIGINT, TEXT, TEXT, JSONB, TEXT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_approve_order(INTEGER, BIGINT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_reject_order(INTEGER)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_mark_order_paid(INTEGER, TEXT, TEXT)
  TO anon, authenticated;

-- Bot Telegram orqali o'z autentifikatsiyasini tekshiradi. Anon key bilan
-- ishlashi uchun PostgREST rollariga jadval siyosatlari kerak.
-- Productionda SUPABASE_SERVICE_ROLE_KEY ishlatish xavfsizroq.
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "bot_products_access" ON products;
DROP POLICY IF EXISTS "bot_orders_access" ON orders;
DROP POLICY IF EXISTS "bot_order_items_access" ON order_items;
DROP POLICY IF EXISTS "bot_transactions_access" ON transactions;

CREATE POLICY "bot_products_access" ON products
  FOR ALL TO anon, authenticated USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "bot_orders_access" ON orders
  FOR ALL TO anon, authenticated USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "bot_order_items_access" ON order_items
  FOR ALL TO anon, authenticated USING (TRUE) WITH CHECK (TRUE);
CREATE POLICY "bot_transactions_access" ON transactions
  FOR ALL TO anon, authenticated USING (TRUE) WITH CHECK (TRUE);
