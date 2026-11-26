"""SHA-256 image fingerprints used to key saved demo results."""
import hashlib


def sha256_hex(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()
