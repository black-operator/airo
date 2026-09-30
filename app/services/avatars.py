from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError


class AvatarError(ValueError):
    pass


def save_avatar(upload, prefix):
    if not upload or not upload.filename:
        return None
    if upload.mimetype not in current_app.config["ALLOWED_IMAGE_TYPES"]:
        raise AvatarError("Bitte verwende ein JPG-, PNG- oder WebP-Bild.")

    try:
        image = Image.open(upload.stream)
        image.verify()
        upload.stream.seek(0)
        image = Image.open(upload.stream)
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise AvatarError("Das Bild konnte nicht gelesen werden.") from None

    width, height = image.size
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    image = image.crop((left, top, left + edge, top + edge))
    image = image.resize((512, 512), Image.Resampling.LANCZOS)

    filename = f"{prefix}-{uuid4().hex}.webp"
    destination = Path(current_app.config["UPLOAD_FOLDER"]) / filename
    image.save(destination, "WEBP", quality=88, method=6)
    return filename


def delete_avatar(filename):
    if not filename:
        return
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    candidate = (upload_root / Path(filename).name).resolve()
    if candidate.parent == upload_root and candidate.exists():
        candidate.unlink()
