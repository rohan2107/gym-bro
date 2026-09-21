"""Local checks on an uploaded image, run before any provider is called.

Shared by every food-recognition provider, so a bad upload is rejected the same way
regardless of which one is configured, and never costs a provider request.
"""

import io
import logging
from typing import Any, Dict

from PIL import Image


logger = logging.getLogger(__name__)

# ISO base media "ftyp" brands used by HEIC/HEIF images (iPhone and macOS Photos).
_HEIF_BRANDS = frozenset(
    {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"}
)

HEIF_UNSUPPORTED_MESSAGE = (
    "HEIC photos are not supported. Use JPEG or PNG instead: on iPhone, set "
    "Settings > Camera > Formats > Most Compatible; on a Mac, export from Photos "
    "as JPEG."
)


def is_heif(image_bytes: bytes) -> bool:
    """True if the bytes look like a HEIC/HEIF image.

    Pillow cannot decode these without an extra native library, and the failure
    it raises is unhelpful, so they are recognised by signature and rejected with
    a message the user can act on.
    """
    return image_bytes[4:8] == b"ftyp" and image_bytes[8:12] in _HEIF_BRANDS


def validate_image(image_bytes: bytes) -> Dict[str, Any]:
    """Check that an image is suitable for food detection.

    Args:
        image_bytes: Raw image data.

    Returns:
        ``{"valid": True, "format": ..., "size_kb": ..., "dimensions": ...}``
        or ``{"valid": False, "error": ...}``.
    """
    if is_heif(image_bytes):
        return {"valid": False, "error": HEIF_UNSUPPORTED_MESSAGE}

    try:
        image = Image.open(io.BytesIO(image_bytes))
        size_kb = len(image_bytes) / 1024

        # Check file size (max 10MB)
        if size_kb > 10 * 1024:
            return {
                "valid": False,
                "error": "Image too large. Maximum size is 10MB.",
            }

        # Check format
        if image.format.lower() not in ["jpeg", "jpg", "png", "webp"]:
            return {
                "valid": False,
                "error": f"Unsupported format: {image.format}. Use JPEG, PNG, or WebP.",
            }

        # Check dimensions (reasonable size)
        if image.width < 200 or image.height < 200:
            return {
                "valid": False,
                "error": "Image too small. Minimum size is 200x200 pixels.",
            }

        return {
            "valid": True,
            "format": image.format.lower(),
            "size_kb": round(size_kb, 2),
            "dimensions": f"{image.width}x{image.height}",
        }

    except Exception:
        # Pillow's message includes object reprs and is not for users.
        logger.warning("Image validation failed", exc_info=True)
        return {
            "valid": False,
            "error": "Invalid image file. Please upload a JPEG, PNG or WebP photo.",
        }
