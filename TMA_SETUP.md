# TATU Telegram Mini App ishga tushirish

## 1. Database

Supabase SQL Editor'da `supabase/schema.sql` faylini to'liq ishga tushiring.
Skript mavjud jadvallarga TMA ustunlarini qo'shadi:

- `products.category`, `sizes`, `colors`, `image_urls`
- `orders.comment`
- `order_items.size`, `color`
- atomik order/stock RPC funksiyalari

Supabase Storage'da `product-images` nomli **public bucket** yarating.
Admin TMA mahsulot qo'shishda URL yoki rasm faylini shu bucket'ga yuklaydi.

## 2. Environment

`.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
BOT_TOKEN=...
ADMIN_IDS=7736700647
WEBAPP_URL=https://frontend.example.com
WEBAPI_URL=https://api.example.com
WEBAPP_ORIGINS=https://frontend.example.com
```

`SUPABASE_SERVICE_ROLE_KEY` faqat bot/API serverda bo'ladi. Uni frontend
`.env` yoki Git repository'ga qo'ymang. Agar service key bo'lmasa, hozirgi
anon-policy konfiguratsiyasi ishlaydi, lekin production uchun service key
tavsiya etiladi.

`WEBAPP_URL` HTTPS bo'lishi shart. Telegram `http://localhost` Web App'ni
ochmaydi.

## 3. Backend va bot

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_all.bat
```

API health:

```text
GET http://localhost:8000/health
```

## 4. Frontend

```powershell
cd webapp
Copy-Item .env.example .env
# .env ichida VITE_API_URL=https://api.example.com yozing
npm install
npm run build
```

`webapp/dist` papkasini HTTPS hostingga joylashtiring. Keyin `.env` dagi
`WEBAPP_URL` ni shu manzilga qo'yib botni qayta ishga tushiring. Botdagi
`🛍 Do'konni ochish` tugmasi shundan keyin ko'rinadi.

## InitData xavfsizligi

Frontend Supabase key ishlatmaydi. Har bir API so'roviga Telegram `initData`
`X-Telegram-Init-Data` headerida yuboriladi; `web_api.py` uni `BOT_TOKEN`
orqali HMAC-SHA256 bilan tekshiradi. Admin endpointlar qo'shimcha ravishda
`ADMIN_IDS` bilan tekshiriladi.
