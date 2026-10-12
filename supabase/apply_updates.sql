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
  ALTER TABLE public.orders DROP CONSTRAINT IF EXISTS orders_status_check;
  ALTER TABLE public.orders
    ADD CONSTRAINT orders_status_check
    CHECK (status IN ('pending', 'paid', 'approved', 'delivered', 'rejected'));
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

-- ── Foydalanuvchi tili ────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.users (
  user_id       BIGINT PRIMARY KEY,
  language_code VARCHAR(5) NOT NULL DEFAULT 'uz',
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.users TO anon, authenticated;

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "bot_users_access" ON public.users;
CREATE POLICY "bot_users_access" ON public.users
  FOR ALL TO anon, authenticated USING (TRUE) WITH CHECK (TRUE);

GRANT EXECUTE ON FUNCTION shop_stock_in(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;
GRANT EXECUTE ON FUNCTION shop_write_off(INTEGER, INTEGER, BIGINT, TEXT)
  TO anon, authenticated;

-- ── Mahsulot tarjimalari (bo'sh bo'lsa to'ldiriladi) ──
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS name_ru TEXT NOT NULL DEFAULT '';
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS name_en TEXT NOT NULL DEFAULT '';
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS description_ru TEXT NOT NULL DEFAULT '';
ALTER TABLE public.products ADD COLUMN IF NOT EXISTS description_en TEXT NOT NULL DEFAULT '';

UPDATE public.products SET
  name_ru = 'Кепка с логотипом',
  name_en = 'Cap with logo',
  description_ru = 'Официальная кепка бренда ТУИТ',
  description_en = 'Official TUIT brand cap'
WHERE name = 'Logotipli kepka'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Футболка с логотипом',
  name_en = 'T-shirt with logo',
  description_ru = 'Хлопковая футболка с логотипом ТУИТ',
  description_en = 'Cotton T-shirt with the TUIT logo'
WHERE name = 'Logotipli futbolka'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Футболка TERRO PRO с логотипом',
  name_en = 'TERRO PRO T-shirt with logo',
  description_ru = 'Качественная брендовая футболка TERRO PRO',
  description_en = 'Quality TERRO PRO brand T-shirt'
WHERE name = 'Logotipli futbolka TERRO PRO'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Маска с логотипом',
  name_en = 'Face mask with logo',
  description_ru = 'Тканевая маска бренда ТУИТ',
  description_en = 'TUIT brand fabric mask'
WHERE name = 'Logotipli niqob'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Рюкзак с логотипом',
  name_en = 'Backpack with logo',
  description_ru = 'Качественный студенческий рюкзак',
  description_en = 'Quality student backpack'
WHERE name = 'Logotipli ryukzak'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Кружка с логотипом',
  name_en = 'Mug with logo',
  description_ru = 'Керамическая кружка с логотипом ТУИТ',
  description_en = 'Ceramic mug with the TUIT logo'
WHERE name = 'Logotipli krujka'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Термос с логотипом',
  name_en = 'Thermos with logo',
  description_ru = 'Металлический термос, сохраняющий температуру',
  description_en = 'Insulated metal thermos'
WHERE name = 'Logotipli termos'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Зонт с логотипом (большой)',
  name_en = 'Large umbrella with logo',
  description_ru = 'Прочный зонт с логотипом ТУИТ',
  description_en = 'Sturdy umbrella with the TUIT logo'
WHERE name = 'Logotipli soyabon (katta)'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Зонт с логотипом (компактный)',
  name_en = 'Compact umbrella with logo',
  description_ru = 'Компактный зонт с логотипом ТУИТ',
  description_en = 'Compact umbrella with the TUIT logo'
WHERE name = 'Logotipli soyabon (ixcham)'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Пауэрбанк с логотипом',
  name_en = 'Power bank with logo',
  description_ru = 'Портативное зарядное устройство',
  description_en = 'Portable power bank'
WHERE name = 'Logotipli quvvatlagich'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Флешка с логотипом',
  name_en = 'USB flash drive with logo',
  description_ru = 'Брендовая USB-флешка',
  description_en = 'Branded USB flash drive'
WHERE name = 'Logotipli fleshka'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Ручка с логотипом',
  name_en = 'Pen with logo',
  description_ru = 'Официальная ручка ТУИТ',
  description_en = 'Official TUIT pen'
WHERE name = 'Logotipli ruchka'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Чехол с логотипом',
  name_en = 'Case with logo',
  description_ru = 'Специальный брендовый чехол',
  description_en = 'Special brand case'
WHERE name = 'Logotipli g‘ilof'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Визитница с логотипом',
  name_en = 'Card holder with logo',
  description_ru = 'Качественная кожаная визитница',
  description_en = 'Quality leather card holder'
WHERE name = 'Logotipli vizitka g‘ilofi'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Коврик для мыши с логотипом',
  name_en = 'Mouse pad with logo',
  description_ru = 'Брендовый коврик для мыши',
  description_en = 'Branded mouse pad'
WHERE name = 'Logotipli gilamcha'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Блокнот с логотипом',
  name_en = 'Notebook with logo',
  description_ru = 'Блокнот ТУИТ',
  description_en = 'TUIT notebook'
WHERE name = 'Logotipli bloknot'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Ежедневник с логотипом',
  name_en = 'Diary with logo',
  description_ru = 'Официальный ежедневник в твёрдой обложке',
  description_en = 'Official hardcover diary'
WHERE name = 'Logotipli kundalik'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Брелок с логотипом (металл)',
  name_en = 'Metal keychain with logo',
  description_ru = 'Металлический брелок',
  description_en = 'Metal keychain'
WHERE name = 'Logotipli brelok (metall)'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Брелок с логотипом (стандарт)',
  name_en = 'Standard keychain with logo',
  description_ru = 'Стандартный брелок для ключей',
  description_en = 'Standard keychain'
WHERE name = 'Logotipli brelok (standart)'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Часы с логотипом',
  name_en = 'Clock with logo',
  description_ru = 'Настенные или настольные часы',
  description_en = 'Wall or desk clock'
WHERE name = 'Logotipli soat'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Подарочный набор с логотипом',
  name_en = 'Gift set with logo',
  description_ru = 'Основной брендовый подарочный набор',
  description_en = 'Main brand gift set'
WHERE name = 'Logotipli sovg‘a to‘plami'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Подарочный набор с логотипом — стандарт',
  name_en = 'Standard gift set with logo',
  description_ru = 'Стандартный подарочный набор',
  description_en = 'Standard bundled gift set'
WHERE name = 'Logotipli sovg‘a to‘plami — standart'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Подарочный набор с логотипом — расширенный',
  name_en = 'Extended gift set with logo',
  description_ru = 'Расширенный мерч-набор',
  description_en = 'Extended merch set'
WHERE name = 'Logotipli sovg‘a to‘plami — kengaytirilgan'
  AND COALESCE(name_ru, '') = '';

UPDATE public.products SET
  name_ru = 'Подарочный набор с логотипом — премиум',
  name_en = 'Premium gift set with logo',
  description_ru = 'Эксклюзивный премиум-набор',
  description_en = 'Exclusive premium gift set'
WHERE name = 'Logotipli sovg‘a to‘plami — premium'
  AND COALESCE(name_ru, '') = '';
UPDATE public.products SET
  name_ru = 'Ручка',
  name_en = 'Pen',
  description_ru = 'Хорошая ручка',
  description_en = 'A good pen'
WHERE name = 'Ruchka'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Ручка ТУИТ',
  name_en = 'TUIT pen',
  description_ru = 'Премиальная ручка бренда ТУИТ',
  description_en = 'Premium TUIT brand pen'
WHERE name = 'TATU ruchka'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Набор стикеров',
  name_en = 'Sticker pack',
  description_ru = 'Набор стикеров ТУИТ',
  description_en = 'TUIT sticker pack'
WHERE name = 'Stiker to''plami'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Ручка (ТУИТ)',
  name_en = 'Pen (TUIT)',
  description_ru = 'Ручка бренда ТУИТ',
  description_en = 'TUIT brand pen'
WHERE name = 'Ruchka (TATU)'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Белая кепка',
  name_en = 'White cap',
  description_ru = 'Белая кепка бренда ТУИТ',
  description_en = 'White TUIT brand cap'
WHERE name = 'Oq kepka'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Маска',
  name_en = 'Face mask',
  description_ru = 'Маска бренда ТУИТ',
  description_en = 'TUIT brand mask'
WHERE name = 'Niqob'
  AND COALESCE(name_en, '') = '';

UPDATE public.products SET
  name_ru = 'Блокнот',
  name_en = 'Notebook',
  description_ru = 'Блокнот бренда ТУИТ',
  description_en = 'TUIT brand notebook'
WHERE name = 'Bloknot'
  AND COALESCE(name_en, '') = '';

