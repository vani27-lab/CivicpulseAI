import uuid
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("multipart")
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.modules.complaint_engine.router import build_router  # noqa: E402
from tests.helpers import FakeEmbedder, make  # noqa: E402

JPEG = b"\xff\xd8\xff\xe0" + b"x" * 16


def client(officer=None):
    p, repo, _ = make(embedder=FakeEmbedder({JPEG: [1.0, 0.0]}))
    app = FastAPI()
    app.include_router(build_router(lambda: p, officer_dependency=(lambda: officer) if officer else None))
    return TestClient(app), p, repo


def _post(c, lat="27.4924", lon="77.6737"):
    return c.post("/complaints/process", files={"image": ("a.jpg", JPEG, "image/jpeg")},
                  data={"latitude": lat, "longitude": lon, "gps_accuracy": "10"})


def test_process_and_priority_and_duplicates():
    c, _, _ = client()
    r = _post(c)
    assert r.status_code == 200 and r.json()["duplicate_status"] == "new"
    cid = r.json()["complaint_id"]
    assert c.get(f"/complaints/{cid}/priority").status_code == 200
    assert c.get(f"/complaints/{cid}/duplicates").json()["report_count"] == 1
    assert c.get(f"/complaints/{uuid.uuid4()}/priority").status_code == 404


def test_invalid_gps_is_422():
    c, _, _ = client()
    assert _post(c, "0", "0").status_code == 422


def test_split_disabled_without_officer_auth():
    c, _, _ = client()
    cid = _post(c).json()["complaint_id"]
    r = c.post(f"/complaints/{cid}/split", json={"report_ids": [str(uuid.uuid4())]})
    assert r.status_code == 503


def test_split_requires_officer_role():
    c, _, _ = client(officer=SimpleNamespace(id=uuid.uuid4(), role="citizen"))
    cid = _post(c).json()["complaint_id"]
    assert c.post(f"/complaints/{cid}/split", json={"report_ids": [str(uuid.uuid4())]}).status_code == 403


def test_split_end_to_end_as_officer():
    c, _, repo = client(officer=SimpleNamespace(id=uuid.uuid4(), role="officer"))
    cid = _post(c).json()["complaint_id"]
    _post(c)  # merged (identical image + embedder returns same vector)
    rep_ids = [str(r.id) for r in repo.get_reports(uuid.UUID(cid))]
    r = c.post(f"/complaints/{cid}/split", json={"report_ids": rep_ids[:1], "comment": "x"})
    assert r.status_code == 200 and r.json()["new_report_count"] == 1
    assert c.post(f"/complaints/{cid}/split", json={"report_ids": rep_ids}).status_code in (404, 409)
