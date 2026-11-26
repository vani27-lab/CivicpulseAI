"""After-photo validation and storage. Standard library only."""
import os
import re
import uuid
from dataclasses import dataclass

from .errors import UploadError

_SAFE_ID = re.compile(r"[^A-Za-z0-9_-]")


@dataclass(frozen=True)
class ValidatedImage:
    data: bytes
    content_type: str
    extension: str


@dataclass(frozen=True)
class StoredFile:
    url: str
    relative_path: str


def sniff_image_type(data: bytes) -> tuple[str, str] | None:
    """Identify the image from its magic bytes (never trust the filename or client MIME)."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def validate_image(data: bytes, max_bytes: int) -> ValidatedImage:
    if not data:
        raise UploadError("empty_upload", "The uploaded file is empty.")
    if len(data) > max_bytes:
        raise UploadError("file_too_large", f"The photo must be {max_bytes // (1024 * 1024)} MB or smaller.", 413)
    sniffed = sniff_image_type(data)
    if sniffed is None:
        raise UploadError("unsupported_type", "Upload a JPEG, PNG or WebP photo.", 415)
    return ValidatedImage(data=data, content_type=sniffed[0], extension=sniffed[1])


class LocalStorage:
    """Stores after-photos under ``<upload_dir>/after/<complaint_id>/``.

    Swap this class for an S3/MinIO implementation with the same two methods if
    Module 1 already provides object storage.
    """

    def __init__(self, upload_dir: str, media_base_url: str):
        self.upload_dir = upload_dir
        self.media_base_url = media_base_url.rstrip("/")

    def save(self, complaint_id, image: ValidatedImage) -> StoredFile:
        safe_id = _SAFE_ID.sub("", str(complaint_id))
        if not safe_id:
            raise UploadError("bad_complaint_id", "Invalid complaint identifier.")
        relative = os.path.join("after", safe_id, f"{uuid.uuid4().hex}.{image.extension}")
        absolute = os.path.join(self.upload_dir, relative)
        os.makedirs(os.path.dirname(absolute), exist_ok=True)
        with open(absolute, "wb") as handle:
            handle.write(image.data)
        return StoredFile(url=f"{self.media_base_url}/{relative.replace(os.sep, '/')}", relative_path=relative)

    def delete(self, relative_path: str) -> None:
        absolute = os.path.normpath(os.path.join(self.upload_dir, relative_path))
        root = os.path.normpath(self.upload_dir)
        if absolute.startswith(root + os.sep) and os.path.isfile(absolute):
            os.remove(absolute)
