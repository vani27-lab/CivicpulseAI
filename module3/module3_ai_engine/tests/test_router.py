import pytest

pytest.importorskip("fastapi")
pytest.importorskip("multipart")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.modules.ai_engine.router import build_router  # noqa: E402
from tests.conftest import JPEG, good_json  # noqa: E402


def _client(classifier):
    app = FastAPI()
    app.include_router(build_router(classifier_provider=lambda: classifier))
    return TestClient(app)


def test_classify_endpoint(make_classifier):
    c, _ = make_classifier(good_json())
    r = _client(c).post("/ai/classify", files={"image": ("a.jpg", JPEG, "image/jpeg")},
                        data={"description": "pothole"})
    assert r.status_code == 200
    assert r.json()["issue_type"] == "pothole" and r.json()["source"] == "live_ai"


def test_oversize_rejected(make_classifier):
    c, _ = make_classifier(good_json())
    big = JPEG + b"0" * (c.settings.max_image_bytes + 1)
    r = _client(c).post("/ai/classify", files={"image": ("a.jpg", big, "image/jpeg")})
    assert r.status_code == 413


def test_missing_image_is_422(make_classifier):
    c, _ = make_classifier()
    assert _client(c).post("/ai/classify", data={"description": "x"}).status_code == 422
