import math
import uuid
from datetime import datetime, timedelta, timezone

from app.modules.complaint_engine.config import Settings
from app.modules.complaint_engine.domain import ReportInput
from app.modules.complaint_engine.engine import ComplaintProcessor
from app.modules.complaint_engine.places import NullPlaceProvider
from app.modules.complaint_engine.repository_memory import InMemoryComplaintRepository

LAT, LON = 27.4924, 77.6737          # inside the default India bounding box
T0 = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)

DEPTS = {n: uuid.uuid4() for n in ("Roads", "Sanitation", "Electrical", "Drainage", "Manual review")}


def vec(similarity: float):
    """Unit vector whose cosine similarity with [1, 0] equals `similarity`."""
    return [similarity, math.sqrt(max(0.0, 1 - similarity ** 2))]


class FakeEmbedder:
    def __init__(self, table=None):
        self.table = table or {}

    def embed(self, image_bytes):
        return self.table.get(image_bytes)


class Clock:
    def __init__(self, t=T0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


def ai(issue_type="pothole", severity=3, confidence=0.9, **kw):
    d = dict(issue_type=issue_type, severity=severity, confidence=confidence, reason="r",
             detected_language="en", original_text="", translated_text="", needs_review=confidence < 0.7,
             source="live_ai")
    d.update(kw)
    return d


class FakeClassifier:
    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result or ai(), error, 0

    def __call__(self, image_bytes, description, language=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def make(classifier=None, embedder=None, places=None, settings=None, departments=DEPTS):
    repo = InMemoryComplaintRepository(departments)
    clock = Clock()
    proc = ComplaintProcessor(repo, classifier or FakeClassifier(), embedder or FakeEmbedder(),
                              places or NullPlaceProvider(), settings or Settings(), clock)
    return proc, repo, clock


def report(image=b"img-a", lat=LAT, lon=LON, **kw):
    return ReportInput(image_bytes=image, latitude=lat, longitude=lon, description="d", **kw)
