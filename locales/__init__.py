"""Til kodlari va matn olish."""

from locales.texts import TEXTS

LANGS = ("uz", "ru", "en")

_LEGACY_BUTTONS = {
  "btn_orders": {"📦 Mening buyurtmalarim"},
}


def normalize_lang(lang: str | None) -> str:
  return lang if lang in TEXTS else "uz"


def t(lang: str | None, key: str, **kwargs: object) -> str:
  """texts[lang][key]. Topilmasa o'zbekcha, u ham bo'lmasa kalitning o'zi."""
  code = normalize_lang(lang)
  template = TEXTS[code].get(key) or TEXTS["uz"].get(key) or key
  if not kwargs:
    return template
  return template.format(**kwargs)


def button_values(key: str) -> set[str]:
  """Reply tugma matni uch tilda — filtrlar shu to'plamga tayanadi."""
  values = {TEXTS[code][key] for code in TEXTS}
  values.update(_LEGACY_BUTTONS.get(key, ()))
  return values
