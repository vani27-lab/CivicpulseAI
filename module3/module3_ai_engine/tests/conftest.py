import json
from pathlib import Path

import pytest

from app.modules.ai_engine.config import Settings
from app.modules.ai_engine.demo_store import DemoResultStore
from app.modules.ai_engine.exceptions import VisionAPIError
from app.modules.ai_engine.service import ComplaintClassifier

JPEG = b"\xff\xd8\xff\xe0" + b"fakejpegdata" * 4


class FakeClient:
    """Returns queued replies in order; Exception instances are raised."""
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = 0

    def analyze(self, image_bytes, media_type, prompt):
        self.calls += 1
        item = self.replies.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def good_json(**over):
    data = {"issue_type": "pothole", "severity": 3, "confidence": 0.82,
            "reason": "Large visible pothole on the road", "detected_language": "en",
            "translated_text": ""}
    data.update(over)
    return json.dumps(data)


@pytest.fixture
def make_classifier(tmp_path: Path):
    def _make(*replies, demo=None):
        path = tmp_path / "demo.json"
        path.write_text(json.dumps(demo or {}), encoding="utf-8")
        settings = Settings(demo_results_path=str(path))
        client = FakeClient(*replies)
        return ComplaintClassifier(settings, client, DemoResultStore(str(path))), client
    return _make


@pytest.fixture
def api_down():
    return VisionAPIError("down")
