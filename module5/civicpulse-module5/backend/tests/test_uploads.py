import os

import pytest

from app.officer.errors import UploadError
from app.officer.uploads import LocalStorage, sniff_image_type, validate_image

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


def test_sniffs_supported_types():
    assert sniff_image_type(JPEG) == ("image/jpeg", "jpg")
    assert sniff_image_type(PNG) == ("image/png", "png")
    assert sniff_image_type(WEBP) == ("image/webp", "webp")


def test_rejects_non_images_even_with_image_name():
    with pytest.raises(UploadError) as exc:
        validate_image(b"<?php echo 1; ?>", 1024)
    assert exc.value.code == "unsupported_type"


def test_rejects_empty_and_oversized():
    with pytest.raises(UploadError) as exc:
        validate_image(b"", 1024)
    assert exc.value.code == "empty_upload"
    with pytest.raises(UploadError) as exc:
        validate_image(JPEG, 10)
    assert exc.value.code == "file_too_large"
    assert exc.value.status_code == 413


def test_storage_roundtrip(tmp_path):
    storage = LocalStorage(str(tmp_path), "/media")
    image = validate_image(PNG, 4096)
    saved = storage.save("123e4567-e89b-12d3-a456-426614174000", image)
    assert saved.url.startswith("/media/after/123e4567-e89b-12d3-a456-426614174000/")
    assert saved.url.endswith(".png")
    assert os.path.isfile(os.path.join(str(tmp_path), saved.relative_path))
    storage.delete(saved.relative_path)
    assert not os.path.exists(os.path.join(str(tmp_path), saved.relative_path))


def test_storage_sanitises_id_and_blocks_path_escape(tmp_path):
    storage = LocalStorage(str(tmp_path / "up"), "/media")
    image = validate_image(JPEG, 4096)
    saved = storage.save("../../etc", image)
    assert ".." not in saved.relative_path
    outside = tmp_path / "secret.txt"
    outside.write_text("keep")
    storage.delete("../secret.txt")
    assert outside.exists()
