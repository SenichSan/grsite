from __future__ import annotations

import os
from typing import Optional

from django import template
from django.core.files.storage import default_storage
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.contrib.staticfiles import finders

register = template.Library()


def _variant_name(orig_name: str, size: str, ext: str) -> str:
    root, _ext = os.path.splitext(orig_name)
    return f"{root}_{size}.{ext}"


def _url_if_exists(name: str) -> Optional[str]:
    try:
        if default_storage.exists(name):
            return default_storage.url(name)
    except Exception:
        return None
    return None


@register.simple_tag
def category_icon_picture(category, size: str = "128x128", classes: str = "", alt: Optional[str] = None,
                          width: int = 128, height: int = 128):
    """
    Render a <picture> for category.image with AVIF/WebP priority and fallback to original.
    Usage:
      {% category_icon_picture category '128x128' 'catalog-category-icon' category.name 128 128 %}
    """
    img_field = getattr(category, "image", None)
    alt_attr = alt or getattr(category, "name", "")
    class_attr = classes or ""

    # 1) Prefer media-based image from admin with our generated variants
    if img_field and getattr(img_field, "name", ""):
        orig_url = getattr(img_field, "url", None)
        if callable(orig_url):
            try:
                orig_url = img_field.url
            except Exception:
                orig_url = None

        name = img_field.name
        avif_name = _variant_name(name, size, "avif")
        webp_name = _variant_name(name, size, "webp")

        avif_url = _url_if_exists(avif_name)
        webp_url = _url_if_exists(webp_name)

        parts = ["<picture>"]
        if avif_url:
            parts.append(f"<source srcset=\"{avif_url}\" type=\"image/avif\">")
        if webp_url:
            parts.append(f"<source srcset=\"{webp_url}\" type=\"image/webp\">")
        # Fallback to original media image
        if orig_url:
            parts.append(
                f"<img src=\"{orig_url}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"lazy\" decoding=\"async\">"
            )
        parts.append("</picture>")
        return mark_safe("".join(parts))

    # 2) Fallback to static icon by slug (if exists)
    slug = getattr(category, "slug", "")
    if slug:
        static_base = f"deps/icons/{slug}"
        static_avif = f"{static_base}.avif"
        static_webp = f"{static_base}.webp"
        static_png = f"{static_base}.png"
        has_avif = bool(finders.find(static_avif))
        has_webp = bool(finders.find(static_webp))
        has_png = bool(finders.find(static_png))
        if has_avif or has_webp or has_png:
            parts = ["<picture>"]
            if has_avif:
                parts.append(f"<source srcset=\"{ static(static_avif) }\" type=\"image/avif\">")
            if has_webp:
                parts.append(f"<source srcset=\"{ static(static_webp) }\" type=\"image/webp\">")
            fallback = static(static_png) if has_png else (static(static_webp) if has_webp else static(static_avif))
            parts.append(
                f"<img src=\"{fallback}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"lazy\" decoding=\"async\">"
            )
            parts.append("</picture>")
            return mark_safe("".join(parts))

    # 3) Ultimate placeholder
    fallback = static("deps/images/placeholder.png")
    return mark_safe(
        f"<img src=\"{fallback}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"lazy\" decoding=\"async\">"
    )
