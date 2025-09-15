from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class ManifestStaticFilesStorageLoose(ManifestStaticFilesStorage):
    """
    Same as Django's ManifestStaticFilesStorage but does not fail hard when a
    referenced file (e.g., *.map, legacy image URL in CSS) is missing.

    This keeps filename hashing for cache-busting, but if a referenced asset
    isn't present in the manifest, it will fall back to the original URL
    instead of raising ValueError during collectstatic post-processing.
    """

    manifest_strict = False
