"""CLIP image embeddings. Heavy dependencies are imported lazily (see requirements-clip.txt)."""
import io
import logging
from typing import List, Optional, Protocol

logger = logging.getLogger(__name__)


class ImageEmbedder(Protocol):
    def embed(self, image_bytes: bytes) -> Optional[List[float]]:
        """Return an embedding, or None if the image cannot be embedded. Must not raise."""
        ...


class NullEmbedder:
    """No embeddings: nothing can be auto-merged; nearby candidates become 'possible duplicates'."""
    def embed(self, image_bytes: bytes) -> Optional[List[float]]:
        return None


class ClipEmbedder:
    """CLIP via sentence-transformers (default model: clip-ViT-B-32, 512-dim, L2-normalised).

    UNTESTED in the generating environment (no model download/network available).
    """

    def __init__(self, model_name: str = "clip-ViT-B-32"):
        self._name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy: heavy import
            self._model = SentenceTransformer(self._name)
        return self._model

    def embed(self, image_bytes: bytes) -> Optional[List[float]]:
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            vec = self._load().encode(img, normalize_embeddings=True)
            return [float(x) for x in vec]
        except Exception as exc:  # noqa: BLE001 - embedding failure must not block complaint creation
            logger.warning("CLIP embedding failed: %s", type(exc).__name__)
            return None
