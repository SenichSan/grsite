from __future__ import annotations

import os
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage

from .models import Categories, Products, ProductImage
from common.image_utils import generate_icon_variants


def _fs_path_from_storage(name: str) -> str:
    """Resolve absolute filesystem path for a stored file name.
    Works for FileSystemStorage; for others, best-effort using MEDIA_ROOT.
    """
    # default_storage may have .path (FileSystemStorage)
    try:
        return default_storage.path(name)  # type: ignore[attr-defined]
    except Exception:
        return os.path.join(settings.MEDIA_ROOT, name)


@receiver(post_save, sender=Categories)
def categories_generate_icon_variants(sender, instance: Categories, **kwargs):
    """On category save, (re)generate 128x128 AVIF/WebP variants next to original image."""
    image_field = getattr(instance, "image", None)
    if not image_field or not getattr(image_field, "name", ""):
        return
    try:
        src_path = _fs_path_from_storage(image_field.name)
        generate_icon_variants(src_path, size=(128, 128))
    except Exception:
        # Fail silently; this is a best-effort optimization and should not block saving
        pass


@receiver(post_save, sender=Products)
def products_generate_image_variants(sender, instance: Products, **kwargs):
    """On product save, generate WebP/AVIF variants for main image."""
    image_field = getattr(instance, "image", None)
    if not image_field or not getattr(image_field, "name", ""):
        return
    try:
        src_path = _fs_path_from_storage(image_field.name)
        # Generate multiple sizes for responsive images
        generate_icon_variants(src_path, size=(400, 300))  # Card size
        generate_icon_variants(src_path, size=(800, 600))  # Detail page size
    except Exception:
        # Fail silently; this is a best-effort optimization and should not block saving
        pass


@receiver(post_save, sender=ProductImage)
def product_images_generate_variants(sender, instance: ProductImage, **kwargs):
    """On product image save, generate WebP/AVIF variants."""
    image_field = getattr(instance, "image", None)
    if not image_field or not getattr(image_field, "name", ""):
        return
    try:
        src_path = _fs_path_from_storage(image_field.name)
        # Generate multiple sizes for responsive images
        generate_icon_variants(src_path, size=(400, 300))  # Card size
        generate_icon_variants(src_path, size=(800, 600))  # Detail page size
    except Exception:
        # Fail silently; this is a best-effort optimization and should not block saving
        pass
