from __future__ import annotations

import os
from typing import Optional

from django import template
from django.core.files.storage import default_storage
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from django.contrib.staticfiles import finders
from django.conf import settings
import logging

register = template.Library()

logger = logging.getLogger(__name__)


@register.simple_tag
def product_image_picture(product, size: str = "400x300", classes: str = "", alt: Optional[str] = None,
                         width: int = 400, height: int = 300, loading: str = "lazy", fetchpriority: Optional[str] = None):
    """
    Render a <picture> for product image with AVIF/WebP priority and fallback to original.
    Usage:
      {% product_image_picture product '400x300' 'product-card-img' product.name 400 300 'lazy' %}
    """
    alt_attr = alt or getattr(product, "name", "")
    class_attr = classes or ""
    
    # Try main product image first
    img_field = getattr(product, "image", None)
    if not img_field or not getattr(img_field, "name", ""):
        # Try first additional image
        try:
            images = getattr(product, "images", None)
            if images and images.exists():
                img_field = images.first().image
        except Exception:
            pass
    
    if img_field and getattr(img_field, "name", ""):
        orig_url = getattr(img_field, "url", None)
        if callable(orig_url):
            try:
                orig_url = img_field.url
            except Exception:
                orig_url = None

        if orig_url:
            name = img_field.name
            avif_name = _variant_name(name, size, "avif")
            webp_name = _variant_name(name, size, "webp")

            avif_url = _url_if_exists(avif_name)
            webp_url = _url_if_exists(webp_name)

            if getattr(settings, 'DEBUG', False):
                logger.debug("product_image_picture: name=%s size=%s avif=%s webp=%s orig=%s", name, size, bool(avif_url), bool(webp_url), bool(orig_url))

            parts = ["<picture>"]
            if avif_url:
                parts.append(f"<source srcset=\"{avif_url}\" type=\"image/avif\">")
            if webp_url:
                parts.append(f"<source srcset=\"{webp_url}\" type=\"image/webp\">")
            # Prefer modern fallback in <img>: webp -> avif -> original
            img_src = webp_url or avif_url or orig_url
            fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
            parts.append(
                f"<img src=\"{img_src}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
            )
            parts.append("</picture>")
            return mark_safe("".join(parts))

    # Ultimate fallback to placeholder
    fallback = static("deps/images/placeholder.png")
    fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
    return mark_safe(
        f"<img src=\"{fallback}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
    )


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
def category_best_img_src(category, size: str = "128x128") -> Optional[str]:
    """
    Return the best single URL to be used in <img src> for a category icon of given size.
    Priority: WebP -> AVIF -> original for media-based images; for static icons: WebP -> AVIF -> PNG.
    This is used for <link rel="preload" as="image"> to speed up LCP.
    """
    # 1) Media image attached to category
    img_field = getattr(category, "image", None)
    if img_field and getattr(img_field, "name", ""):
        try:
            orig_url = img_field.url
        except Exception:
            orig_url = None

        name = img_field.name
        avif_name = _variant_name(name, size, "avif")
        webp_name = _variant_name(name, size, "webp")
        webp_url = _url_if_exists(webp_name)
        avif_url = _url_if_exists(avif_name)
        # Prefer modern src for <img>
        return webp_url or avif_url or orig_url

    # 2) Static icon (by slug)
    slug = getattr(category, "slug", "")
    if slug:
        static_base = f"deps/icons/{slug}"
        # Sized first
        static_webp_sized = f"{static_base}_{size}.webp"
        static_avif_sized = f"{static_base}_{size}.avif"
        # Non-sized fallback
        static_webp = f"{static_base}.webp"
        static_avif = f"{static_base}.avif"
        static_png = f"{static_base}.png"

        # Prefer WebP -> AVIF -> PNG (for src attribute compatibility and weight)
        for path in (static_webp_sized, static_avif_sized, static_webp, static_avif, static_png):
            if finders.find(path):
                return static(path)

    return None


@register.simple_tag
def category_icon_picture(category, size: str = "128x128", classes: str = "", alt: Optional[str] = None,
                          width: int = 128, height: int = 128, loading: str = "lazy", fetchpriority: Optional[str] = None):
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

        if getattr(settings, 'DEBUG', False):
            logger.debug("category_icon_picture: name=%s size=%s avif=%s webp=%s orig=%s", name, size, bool(avif_url), bool(webp_url), bool(orig_url))

        parts = ["<picture>"]
        if avif_url:
            parts.append(f"<source srcset=\"{avif_url}\" type=\"image/avif\">")
        if webp_url:
            parts.append(f"<source srcset=\"{webp_url}\" type=\"image/webp\">")
        # Prefer modern fallback in <img>: webp -> avif -> original
        if orig_url or webp_url or avif_url:
            img_src = webp_url or avif_url or orig_url
            fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
            parts.append(
                f"<img src=\"{img_src}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
            )
        parts.append("</picture>")
        return mark_safe("".join(parts))

    # 2) Fallback to static icon by slug (if exists)
    slug = getattr(category, "slug", "")
    if slug:
        static_base = f"deps/icons/{slug}"
        # Try with size suffix first (generated by generate_category_icons command)
        static_avif_sized = f"{static_base}_{size}.avif"
        static_webp_sized = f"{static_base}_{size}.webp"
        # Fallback to files without size suffix
        static_avif = f"{static_base}.avif"
        static_webp = f"{static_base}.webp"
        static_png = f"{static_base}.png"
        
        # Check for sized variants first, then fallback to non-sized
        has_avif = bool(finders.find(static_avif_sized)) or bool(finders.find(static_avif))
        has_webp = bool(finders.find(static_webp_sized)) or bool(finders.find(static_webp))
        has_png = bool(finders.find(static_png))
        
        # Use the actual found files
        final_avif = static_avif_sized if finders.find(static_avif_sized) else static_avif
        final_webp = static_webp_sized if finders.find(static_webp_sized) else static_webp
        if has_avif or has_webp or has_png:
            parts = ["<picture>"]
            if has_avif:
                parts.append(f"<source srcset=\"{ static(final_avif) }\" type=\"image/avif\">")
            if has_webp:
                parts.append(f"<source srcset=\"{ static(final_webp) }\" type=\"image/webp\">")
            fallback = static(static_png) if has_png else (static(final_webp) if has_webp else static(final_avif))
            fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
            parts.append(
                f"<img src=\"{fallback}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
            )
            parts.append("</picture>")
            return mark_safe("".join(parts))

    # 3) Ultimate placeholder
    fallback = static("deps/images/placeholder.png")
    fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
    return mark_safe(
        f"<img src=\"{fallback}\" alt=\"{alt_attr}\" class=\"{class_attr}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
    )


@register.simple_tag
def field_image_picture(image_field, size: str = "400x300", classes: str = "", alt: str = "",
                        width: int = 400, height: int = 300, loading: str = "lazy", fetchpriority: Optional[str] = None):
    """
    Render <picture> for arbitrary ImageField/FileField with AVIF/WebP priority and fallback.
    Usage:
      {% field_image_picture img.image '400x300' 'class' product.name 400 300 'lazy' %}
    """
    if not image_field or not getattr(image_field, "name", ""):
        fallback = static("deps/images/placeholder.png")
        fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
        return mark_safe(
            f"<img src=\"{fallback}\" alt=\"{alt}\" class=\"{classes}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
        )

    try:
        orig_url = image_field.url
    except Exception:
        orig_url = None

    name = image_field.name
    avif_name = _variant_name(name, size, "avif")
    webp_name = _variant_name(name, size, "webp")

    avif_url = _url_if_exists(avif_name)
    webp_url = _url_if_exists(webp_name)

    if getattr(settings, 'DEBUG', False):
        logger.debug("field_image_picture: name=%s size=%s avif=%s webp=%s orig=%s", name, size, bool(avif_url), bool(webp_url), bool(orig_url))

    parts = ["<picture>"]
    if avif_url:
        parts.append(f"<source srcset=\"{avif_url}\" type=\"image/avif\">")
    if webp_url:
        parts.append(f"<source srcset=\"{webp_url}\" type=\"image/webp\">")
    fp_attr = f" fetchpriority=\"{fetchpriority}\"" if fetchpriority else ""
    img_src = webp_url or avif_url or orig_url or static("deps/images/placeholder.png")
    parts.append(
        f"<img src=\"{img_src}\" alt=\"{alt}\" class=\"{classes}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\" decoding=\"async\"{fp_attr}>"
    )
    parts.append("</picture>")
    return mark_safe("".join(parts))
