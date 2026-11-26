import hashlib
import io

import pytest
from fastapi import HTTPException

from app.services import storage

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 200
PNG = b"\x89PNG\r\n\x1a\n" + b"x" * 200
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"x" * 200


@pytest.fixture(autouse=True)
def temp_upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.settings, "upload_dir", str(tmp_path))
    monkeypatch.setattr(storage.settings, "max_upload_mb", 1)
    return tmp_path


def test_detects_real_types():
    assert storage.detect_image_type(JPEG)[1] == "image/jpeg"
    assert storage.detect_image_type(PNG)[1] == "image/png"
    assert storage.detect_image_type(WEBP)[1] == "image/webp"
    assert storage.detect_image_type(b"hello world") is None


def test_save_image_writes_file_and_fingerprint(temp_upload_dir):
    saved = storage.save_image(io.BytesIO(JPEG))
    assert (temp_upload_dir / saved.relative_path).read_bytes() == JPEG
    assert saved.sha256 == hashlib.sha256(JPEG).hexdigest()
    assert saved.relative_path.startswith("reports/") and saved.relative_path.endswith(".jpg")


def test_rejects_non_image():
    with pytest.raises(HTTPException) as error:
        storage.save_image(io.BytesIO(b"just some text"))
    assert error.value.status_code == 400


def test_rejects_empty_file():
    with pytest.raises(HTTPException) as error:
        storage.save_image(io.BytesIO(b""))
    assert error.value.status_code == 400


def test_rejects_too_large_file():
    with pytest.raises(HTTPException) as error:
        storage.save_image(io.BytesIO(JPEG + b"x" * (1024 * 1024)))
    assert error.value.status_code == 413
