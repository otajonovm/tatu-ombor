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
    "name": "Logotipli kepka",
    "description": "TATU rasmiy brend kepkasi",
    "price": 39000,
    "quantity": 4,
    "image": "oq_kepka.jpg",
  },
  {
    "name": "Logotipli futbolka",
    "description": "TATU logotipi tushirilgan paxta futbolka",
    "price": 99000,
    "quantity": 131,
    "image": "tatu_oq_futbolka.png",
  },
  {
    "name": "Logotipli futbolka TERRO PRO",
    "description": "TERRO PRO sifatli brend futbolka",
    "price": 219000,
    "quantity": 54,
    "image": "tatu_kok_futbolka.png",
  },
  {
    "name": "Logotipli niqob",
    "description": "TATU brendli matoli niqob",
    "price": 19000,
    "quantity": 29,
    "image": "niqob.jpg",
  },
  {
    "name": "Logotipli ryukzak",
    "description": "Sifatli talabalar ryukzaki",
    "price": 349000,
    "quantity": 1,
    "image": "tatu_noutbuk_sumkasi.png",
  },
  {
    "name": "Logotipli krujka",
    "description": "TATU logotipi tushirilgan sopol krujka",
    "price": 49000,
    "quantity": 20,
    "image": "tatu_kupka.png",
  },
  {
    "name": "Logotipli termos",
    "description": "Haroratni saqlovchi metall termos",
    "price": 149000,
    "quantity": 16,
    "image": "tatu_smart_termos.png",
  },
  {
    "name": "Logotipli soyabon (katta)",
    "description": "TATU logotipli mustahkam soyabon (179 000)",
    "price": 179000,
    "quantity": 4,
  },
  {
    "name": "Logotipli soyabon (ixcham)",
    "description": "TATU logotipli ixcham soyabon (159 000)",
    "price": 159000,
    "quantity": 1,
  },
  {
    "name": "Logotipli quvvatlagich",
    "description": "Powerbank / quvvatlovchi qurilma",
    "price": 279000,
    "quantity": 8,
  },
  {
    "name": "Logotipli fleshka",
    "description": "Branded USB flash-xotira",
    "price": 119000,
    "quantity": 0,
  },
  {
    "name": "Logotipli ruchka",
    "description": "TATU rasmiy yozuv ruchkasi",
    "price": 4900,
    "quantity": 150,
    "image": "tatu_bloknot_ruchka.jpg",
  },
  {
    "name": "Logotipli g\u2018ilof",
    "description": "Maxsus brend g\u2018ilof",
    "price": 24900,
    "quantity": 0,
    "image": "tatu_papka_sumka.png",
  },
  {
    "name": "Logotipli vizitka g\u2018ilofi",
    "description": "Sifatli charm vizitnica",
    "price": 39000,
    "quantity": 28,
  },
  {
    "name": "Logotipli gilamcha",
    "description": "Sichqoncha (mouse pad) uchun brend gilamcha",
    "price": 49000,
    "quantity": 32,
  },
  {
    "name": "Logotipli bloknot",
    "description": "TATU yozuv daftari / bloknot",
    "price": 19500,
    "quantity": 48,
    "image": "bloknot.jpg",
  },
  {
    "name": "Logotipli kundalik",
    "description": "Qattiq muqovali rasmiy kundalik (ejednevnik)",
    "price": 59000,
    "quantity": 37,
    "image": "tatu_bloknot_ruchka.jpg",
  },
  {
    "name": "Logotipli brelok (metall)",
    "description": "Metall brelok",
    "price": 35000,
    "quantity": 0,
    "image": "tatu_brelok.jpg",
  },
  {
    "name": "Logotipli brelok (standart)",
    "description": "Standart kalit breloki",
    "price": 10000,
    "quantity": 0,
  },
  {
    "name": "Logotipli soat",
    "description": "Devor / stol soati",
    "price": 110000,
    "quantity": 17,
    "image": "tatu_soat.png",
  },
  {
    "name": "Logotipli sovg\u2018a to\u2018plami",
    "description": "Asosiy brend sovg\u2018a to\u2018plami",
    "price": 1159000,
    "quantity": 8,
    "image": "tatu_brend_tohlami.png",
  },
  {
    "name": "Logotipli sovg\u2018a to\u2018plami \u2014 standart",
    "description": "Standart jamlanmali sovg\u2018a to\u2018plami",
    "price": 1359000,
    "quantity": 26,
    "image": "tatu_brend_tohlami.png",
  },
  {
    "name": "Logotipli sovg\u2018a to\u2018plami \u2014 kengaytirilgan",
    "description": "Kengaytirilgan merch to\u2018plami",
    "price": 1389000,
    "quantity": 18,
  },
  {
    "name": "Logotipli sovg\u2018a to\u2018plami \u2014 premium",
    "description": "Eksklyuziv premium sovg\u2018a to\u2018plami",
    "price": 1599000,
    "quantity": 2,
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
