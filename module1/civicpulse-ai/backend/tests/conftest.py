"""Tests use a throw-away in-memory SQLite database.

Only the `departments` and `users` tables are created because the other tables use
PostGIS (which SQLite does not have). Tests for those tables need a real PostGIS
database and belong to the later modules.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Department, User
from app.models.enums import UserRole


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine, tables=[Department.__table__, User.__table__])
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()

    roads = Department(code="roads", name="Roads")
    session.add(roads)
    session.flush()
    session.add_all([
        User(full_name="Test Admin", email="admin@test.local", hashed_password=hash_password("Password1"), role=UserRole.ADMIN),
        User(full_name="Test Officer", email="officer@test.local", hashed_password=hash_password("Password1"), role=UserRole.OFFICER, department_id=roads.id),
        User(full_name="Test Citizen", email="citizen@test.local", hashed_password=hash_password("Password1"), role=UserRole.CITIZEN),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client, email, password="Password1"):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
