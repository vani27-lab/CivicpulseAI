"""Role-based access tests. Need the web stack: pip install -r requirements-module5.txt"""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.officer import include_module5_routers, integration

PROTECTED = [
    ("GET", "/officer/dashboard/stats"),
    ("GET", "/officer/filters"),
    ("GET", "/officer/complaints"),
    ("GET", "/officer/complaints/duplicates"),
    ("GET", "/officer/complaints/map"),
    ("GET", "/officer/complaints/123e4567-e89b-12d3-a456-426614174000"),
    ("POST", "/officer/duplicates/abc/confirm"),
    ("POST", "/officer/duplicates/abc/reject"),
    ("PATCH", "/complaints/123e4567-e89b-12d3-a456-426614174000/classification"),
    ("POST", "/complaints/123e4567-e89b-12d3-a456-426614174000/split"),
    ("GET", "/stats/heatmap"),
]


def make_client(role):
    app = FastAPI()
    include_module5_routers(app)

    def fake_user():
        if role is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"id": "00000000-0000-0000-0000-000000000009", "name": "T", "role": role}

    app.dependency_overrides[integration.get_current_user] = fake_user
    return TestClient(app)


@pytest.mark.parametrize("method,path", PROTECTED)
def test_citizen_is_forbidden_everywhere(method, path):
    resp = make_client("citizen").request(method, path, json={})
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "forbidden"


@pytest.mark.parametrize("method,path", PROTECTED)
def test_anonymous_is_unauthorised(method, path):
    assert make_client(None).request(method, path, json={}).status_code == 401


def test_status_endpoint_forbidden_for_citizen():
    resp = make_client("citizen").patch(
        "/complaints/123e4567-e89b-12d3-a456-426614174000/status", data={"new_status": "assigned"}
    )
    assert resp.status_code == 403


def test_officer_gets_past_the_role_gate():
    # DB is a stub, so the request fails later - but never with 401/403.
    client = make_client("officer")
    client.raise_server_exceptions = False
    resp = client.get("/officer/complaints/duplicates")
    assert resp.status_code not in (401, 403)
