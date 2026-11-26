"""Saving uploaded photographs to disk.

Files are saved as  uploads/reports/<random-name>.<ext>  (we never use the name the
user gave us). The SHA-256 "fingerprint" is calculated here because Module 3 uses it
to find saved demo AI results.
"""
import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional

from fastapi import HTTPException, status

from app.core.config import settings


@dataclass
class SavedImage:
    relative_path: str  # e.g. "reports/3f2a....jpg" (stored in the database)
    sha256: str
    size_bytes: int
    content_type: str


def detect_image_type(data: bytes) -> Optional[tuple[str, str]]:
    """Look at the first bytes of the file (not the file name) to learn its real type."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None


def save_image(file_obj: BinaryIO) -> SavedImage:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = file_obj.read(max_bytes + 1)  # read one byte extra to detect "too large"

    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The photo is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"The photo is too large. The limit is {settings.max_upload_mb} MB.",
        )
    kind = detect_image_type(data)
    if kind is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please upload a JPEG, PNG or WebP photo.")
    extension, content_type = kind

    relative_path = f"reports/{uuid.uuid4().hex}{extension}"
    full_path = Path(settings.upload_dir) / relative_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(data)

    return SavedImage(
        relative_path=relative_path,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        content_type=content_type,
    )


def delete_image(relative_path: str) -> None:
    """Used to clean up if saving the report fails after the photo was saved."""
    try:
        (Path(settings.upload_dir) / relative_path).unlink(missing_ok=True)
    except OSError:
        pass
