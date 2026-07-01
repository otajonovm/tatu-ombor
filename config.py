import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS: list[int] = [
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

DEFAULT_PRODUCTS = [
    {"name": "Oq kepka", "quantity": 0, "image": "oq_kepka.jpg"},
    {"name": "Niqob", "quantity": 0, "image": "niqob.jpg"},
    {"name": "Stiker to'plami", "quantity": 0, "image": "stiker.jpg"},
    {"name": "Ruchka (TATU)", "quantity": 0, "image": "ruchka.jpg"},
    {"name": "Bloknot", "quantity": 0, "image": "bloknot.jpg"},
]
