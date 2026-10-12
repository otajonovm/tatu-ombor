"""Mahsulot nomi va tavsifini foydalanuvchi tilida olish."""

from locales.product_translations import PRODUCT_TRANSLATIONS


def _saved(product: dict, lang: str | None, field: str) -> str:
  column = f"{field}_{lang}" if lang in {"ru", "en"} else field
  value = str(product.get(column) or "").strip()
  if value:
    return value
  if lang not in {"ru", "en"}:
    return ""
  source_name = str(product.get("name") or product.get("product_name") or "")
  pack = PRODUCT_TRANSLATIONS.get(source_name) or {}
  return str(pack.get(column) or "").strip()


def localized_name(product: dict, lang: str | None) -> str:
  value = _saved(product, lang, "name")
  if value:
    return value
  return str(product.get("name") or product.get("product_name") or "").strip()


def localized_description(product: dict, lang: str | None) -> str:
  value = _saved(product, lang, "description")
  if value:
    return value
  return str(product.get("description") or "").strip()


def translation_for(name: str) -> dict[str, str] | None:
  return PRODUCT_TRANSLATIONS.get(name)
