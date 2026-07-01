from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = Path(__file__).parent.parent / "images"

COLORS = {
  "Oq kepka": (41, 98, 255),
  "Niqob": (76, 175, 80),
  "Stiker to'plami": (255, 152, 0),
  "Ruchka (TATU)": (156, 39, 176),
  "Bloknot": (96, 125, 139),
}


def ensure_product_images(products: list[dict]) -> None:
  IMAGES_DIR.mkdir(exist_ok=True)

  for product in products:
    filename = product.get("image")
    if not filename:
      continue

    path = IMAGES_DIR / filename
    if path.exists():
      continue

    color = COLORS.get(product["name"], (63, 81, 181))
    _create_placeholder(path, product["name"], color)


def _create_placeholder(path: Path, label: str, color: tuple[int, int, int]) -> None:
  img = Image.new("RGB", (512, 512), color)
  draw = ImageDraw.Draw(img)

  try:
    font = ImageFont.truetype("arial.ttf", 36)
  except OSError:
    font = ImageFont.load_default()

  draw.text((256, 256), label, fill="white", font=font, anchor="mm")
  img.save(path, "JPEG", quality=85)
