import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
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
  "approved": "✅ Qabul qilindi",
  "rejected": "❌ Bekor qilindi",
}

TX_TYPE_LABELS = {
  "kirim": "📥 Kirim",
  "sotuv": "🛒 Sotuv",
  "hisobdan_chiqarish": "📤 Hisobdan chiqarish",
}
