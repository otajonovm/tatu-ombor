import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "tatubrandshopbot").strip().lstrip("@")
# Ikkala provayder alohida token. Eski PAYMENTS_PROVIDER_TOKEN faqat Click
# kaliti berilmagan bo'lsa Click sifatida olinadi.
PAYME_PROVIDER_TOKEN = os.getenv("PAYME_PROVIDER_TOKEN", "").strip()
CLICK_PROVIDER_TOKEN = os.getenv("CLICK_PROVIDER_TOKEN", "").strip()
_legacy_payment_token = os.getenv("PAYMENTS_PROVIDER_TOKEN", "").strip()
if (
  not CLICK_PROVIDER_TOKEN
  and _legacy_payment_token
  and _legacy_payment_token != PAYME_PROVIDER_TOKEN
):
  CLICK_PROVIDER_TOKEN = _legacy_payment_token
PAYMENT_CURRENCY = "UZS"
ADMIN_IDS: list[int] = [
  int(x.strip())
  for x in os.getenv("ADMIN_IDS", "").split(",")
  if x.strip().isdigit()
]

# Supabase REST API (supabase-py)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
  os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
  or os.getenv("SUPABASE_ANON_KEY", "").strip()
)
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip().rstrip("/")
WEBAPI_URL = os.getenv("WEBAPI_URL", "http://localhost:8000").strip().rstrip("/")
WEBAPP_ORIGINS = [
  origin.strip().rstrip("/")
  for origin in os.getenv("WEBAPP_ORIGINS", "").split(",")
  if origin.strip()
]
# Vercel preview/prod domenlarini avtomatik qo'shish (CORS)
_extra_origins = os.getenv("WEBAPP_EXTRA_ORIGINS", "").strip()
if _extra_origins:
  WEBAPP_ORIGINS.extend(
    origin.strip().rstrip("/")
    for origin in _extra_origins.split(",")
    if origin.strip()
  )
# Bo'sh bo'lsa CORSMiddleware ["*"] ishlatadi (WEBAPP_ORIGINS or ["*"])
# Brauzerda (Telegram tashqarisida) lokal test uchun. Productionda o'chiring.
TMA_DEV_MODE = os.getenv("TMA_DEV_MODE", "").strip().lower() in {
  "1",
  "true",
  "yes",
  "on",
}

SHOP_NAME = "TATU Brend Do'koni"

SHOP_ABOUT = (
  "🏛 <b>TATU Brend Do'koni</b>\n\n"
  "Rasmiy TATU brend mahsulotlari — kepka, niqob, stiker, "
  "ruchka, bloknot va boshqalar.\n\n"
  "📍 <b>Manzil:</b> TATU (Toshkent axborot texnologiyalari universiteti)\n"
  "📞 <b>Aloqa:</b> @tatu_brent_shop_bot\n"
  "🕒 <b>Ish vaqti:</b> Dushanba–Juma, 09:00–18:00\n\n"
  "Buyurtma berganingizdan so'ng admin tasdiqlaydi."
)

DEFAULT_PRODUCTS = [
  {
    "name": "Oq kepka",
    "description": "TATU brend oq kepka",
    "price": 50000,
    "quantity": 0,
    "image": "oq_kepka.jpg",
  },
  {
    "name": "Niqob",
    "description": "TATU brend niqob",
    "price": 15000,
    "quantity": 0,
    "image": "niqob.jpg",
  },
  {
    "name": "Stiker to'plami",
    "description": "TATU stikerlar to'plami",
    "price": 10000,
    "quantity": 0,
    "image": "stiker.jpg",
  },
  {
    "name": "Ruchka (TATU)",
    "description": "TATU brend ruchka",
    "price": 8000,
    "quantity": 0,
    "image": "ruchka.jpg",
  },
  {
    "name": "Bloknot",
    "description": "TATU brend bloknot",
    "price": 25000,
    "quantity": 0,
    "image": "bloknot.jpg",
  },
]

ORDER_STATUS_LABELS = {
  "pending": "⏳ Kutilmoqda",
  "paid": "💳 To'langan",
  "approved": "✅ Qabul qilindi",
  "rejected": "❌ Bekor qilindi",
}

TX_TYPE_LABELS = {
  "kirim": "📥 Kirim",
  "sotuv": "🛒 Sotuv",
  "hisobdan_chiqarish": "📤 Hisobdan chiqarish",
}
