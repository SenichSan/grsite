from __future__ import annotations

import os
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage

from .models import Categories
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
