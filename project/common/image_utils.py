import os
from io import BytesIO
from typing import Tuple

from PIL import Image

try:
    import pillow_avif  # noqa: F401  # registers AVIF
    AVIF_AVAILABLE = True
except Exception:
    AVIF_AVAILABLE = False


def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _open_image(path: str) -> Image.Image:
    img = Image.open(path)
    img.load()
    return img


def _fit_box(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    # cover-like resize with center crop to exact size
    target_w, target_h = size
    src_w, src_h = img.size
    src_ratio = src_w / src_h if src_h else 1
    tgt_ratio = target_w / target_h if target_h else 1

    if src_ratio > tgt_ratio:
        # source wider -> fit height then crop width
        new_h = target_h
        new_w = int(round(new_h * src_ratio))
    else:
        # source taller -> fit width then crop height
        new_w = target_w
        new_h = int(round(new_w / src_ratio))

    resized = img.convert("RGBA").resize((new_w, new_h), Image.LANCZOS)
    # crop center
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    box = (left, top, left + target_w, top + target_h)
    return resized.crop(box)


def save_webp(img: Image.Image, out_path: str, quality: int = 80) -> None:
    ensure_dir(out_path)
    img.save(out_path, format="WEBP", quality=quality, method=6)


def save_avif(img: Image.Image, out_path: str, quality: int = 32) -> None:
    if not AVIF_AVAILABLE:
        return
    ensure_dir(out_path)
    # pillow-avif uses 'quality' 0..100 similar to JPEG; smaller -> worse
    # we'll map requested 'quality' ~ cqLevel analogue
    img.save(out_path, format="AVIF", quality=quality)


def build_variant_paths(original_path: str, size_name: str, out_ext: str) -> str:
    # /media/categories/foo.png -> /media/categories/foo_<size>.<ext>
    root, _ext = os.path.splitext(original_path)
    return f"{root}_{size_name}.{out_ext}"


def generate_icon_variants(original_fs_path: str, size: Tuple[int, int] = (128, 128)) -> dict:
    """
    Generate WebP and AVIF variants next to original file.
    Returns dict with keys: 'webp', 'avif' (values are absolute FS paths that exist).
    Missing formats may be absent if plugin not available.
    """
    if not original_fs_path or not os.path.exists(original_fs_path):
        return {}

    img = _open_image(original_fs_path)
    fitted = _fit_box(img, size)

    size_name = f"{size[0]}x{size[1]}"

    out = {}

    webp_path = build_variant_paths(original_fs_path, size_name, "webp")
    save_webp(fitted, webp_path, quality=80)
    if os.path.exists(webp_path):
        out["webp"] = webp_path

    if AVIF_AVAILABLE:
        avif_path = build_variant_paths(original_fs_path, size_name, "avif")
        save_avif(fitted, avif_path, quality=32)
        if os.path.exists(avif_path):
            out["avif"] = avif_path

    return out
