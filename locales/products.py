"""Mahsulot nomi va tavsifini foydalanuvchi tilida olish."""

from locales.product_translations import PRODUCT_TRANSLATIONS


def localized_name(product: dict, lang: str | None) -> str:
  if lang == "ru":
    value = str(product.get("name_ru") or "").strip()
  elif lang == "en":
    value = str(product.get("name_en") or "").strip()
  else:
    value = ""
  if value:
    return value
  return str(product.get("name") or product.get("product_name") or "").strip()


def localized_description(product: dict, lang: str | None) -> str:
  if lang == "ru":
    value = str(product.get("description_ru") or "").strip()
  elif lang == "en":
    value = str(product.get("description_en") or "").strip()
  else:
    value = ""
  if value:
    return value
  return str(product.get("description") or "").strip()


def translation_for(name: str) -> dict[str, str] | None:
  return PRODUCT_TRANSLATIONS.get(name)
