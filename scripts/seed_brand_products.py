"""Rasmdagi TATU brend mahsulotlarini Supabase'ga qo'shadi."""

from __future__ import annotations

from supabase_db import add_product, format_price, get_product_by_name

PRODUCTS = [
  {
    "name": "TATU Ko'k futbolka",
    "description": (
      "Muhammad al-Xorazmiy nomidagi TATU logotipi tushirilgan to'q ko'k "
      "rangli sifatli futbolka. Yengida O'zbekiston bayrog'i va TATU yorlig'i bor."
    ),
    "price": 149_000,
    "quantity": 40,
    "image_url": "tatu_kok_futbolka.png",
  },
  {
    "name": "TATU Oq futbolka",
    "description": (
      "TATU rasmiy logotipi tushirilgan oq paxta futbolka. "
      "Yengida bayroq va brend yozuvi bilan."
    ),
    "price": 149_000,
    "quantity": 40,
    "image_url": "tatu_oq_futbolka.png",
  },
  {
    "name": "TATU Sovg'a paketi",
    "description": (
      "TATU logotipli mustahkam ko'k qog'oz paket, oq arqon tutqichli. "
      "Sovg'a va xaridlar uchun."
    ),
    "price": 25_000,
    "quantity": 120,
    "image_url": "tatu_brend_tohlami.png",
  },
  {
    "name": "TATU Premium soat",
    "description": (
      "1955 Edition klassik qo'l soati: to'q ko'k siferblat, charm tasma, "
      "kumushrang korpus. Maxsus baxmal quti bilan."
    ),
    "price": 549_000,
    "quantity": 20,
    "image_url": "tatu_soat.png",
  },
  {
    "name": "TATU Smart termos",
    "description": (
      "LED displeyli aqlli termos — qopqog'ida harorat ko'rsatadi. "
      "TATU logotipi va brend qadoq bilan."
    ),
    "price": 189_000,
    "quantity": 35,
    "image_url": "tatu_smart_termos.png",
  },
  {
    "name": "TATU Brend kupka",
    "description": (
      "To'q ko'k keramik kupka, to'liq rangli TATU gerbi va universitet "
      "nomi bilan. Sovg'a qutisi mos."
    ),
    "price": 59_000,
    "quantity": 80,
    "image_url": "tatu_kupka.png",
  },
  {
    "name": "TATU Noutbuk sumkasi",
    "description": (
      "Professional to'q ko'k noutbuk sumkasi: yelka tasmasi, tutqichlar "
      "va oldingi cho'ntak. Tikilgan TATU gerbi."
    ),
    "price": 279_000,
    "quantity": 30,
    "image_url": "tatu_noutbuk_sumkasi.png",
  },
  {
    "name": "TATU Charm papka",
    "description": (
      "To'q ko'k charm uslubidagi hujjat papkasi. Oltin rangli TATU "
      "yozuvi va 1955 gerbi bilan."
    ),
    "price": 119_000,
    "quantity": 45,
    "image_url": "tatu_papka_sumka.png",
  },
  {
    "name": "TATU Brend bloknot",
    "description": (
      "Qattiq muqovali to'q ko'k kundalik: elastik tasma, lenta xatcho'p "
      "va oltin TATU gerbi."
    ),
    "price": 69_000,
    "quantity": 60,
    "image_url": "tatu_bloknot_ruchka.jpg",
  },
  {
    "name": "TATU Brend ruchka",
    "description": (
      "Oq korpusli, qora aksentli TATU brendli ruchka. "
      "Kundalik va sovg'alar uchun."
    ),
    "price": 12_000,
    "quantity": 200,
    "image_url": "tatu_bloknot_ruchka.jpg",
  },
  {
    "name": "TATU Brend to'plami",
    "description": (
      "Premium sovg'a to'plami: futbolka, paket, kupka, termos, soat, "
      "ruchka va aksessuarlar bitta brend uslubida."
    ),
    "price": 999_000,
    "quantity": 10,
    "image_url": "tatu_brend_tohlami.png",
  },
]


def main() -> None:
  added: list[tuple] = []
  skipped: list[tuple] = []

  for product in PRODUCTS:
    existing = get_product_by_name(product["name"])
    if existing:
      skipped.append((product["name"], existing["id"]))
      continue

    row = add_product(
      name=product["name"],
      description=product["description"],
      price=product["price"],
      quantity=product["quantity"],
      image_url=product["image_url"],
      admin_id=1,
    )
    added.append(
      (row["id"], row["name"], row["price"], row["quantity"], product["image_url"])
    )

  print(f"ADDED {len(added)}")
  for item in added:
    print(
      f"  #{item[0]} | {item[1]} | {format_price(item[2])} | "
      f"{item[3]} dona | {item[4]}"
    )

  print(f"SKIPPED {len(skipped)}")
  for name, product_id in skipped:
    print(f"  {name} (id={product_id})")


if __name__ == "__main__":
  main()
