from tests.conftest import login


def test_login_success_and_me(client):
    headers = login(client, "citizen@test.local")
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["role"] == "citizen"


def test_login_wrong_password(client):
    response = client.post("/api/auth/login", json={"email": "citizen@test.local", "password": "nope"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."


def test_register_creates_citizen_only(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "New Person", "email": "new@test.com", "password": "Password1"},
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "citizen"


def test_register_duplicate_email(client):
    response = client.post(
        "/api/auth/register",
        json={"full_name": "Dup", "email": "citizen@test.local", "password": "Password1"},
    )
    assert response.status_code == 409


def test_me_requires_login(client):
    assert client.get("/api/auth/me").status_code == 401


def test_users_list_is_admin_only(client):
    assert client.get("/api/users", headers=login(client, "citizen@test.local")).status_code == 403
    assert client.get("/api/users", headers=login(client, "officer@test.local")).status_code == 403
    admin = client.get("/api/users", headers=login(client, "admin@test.local"))
    assert admin.status_code == 200
    assert len(admin.json()) == 3


def test_admin_creates_officer_needs_department(client):
    headers = login(client, "admin@test.local")
    body = {"full_name": "Off Icer", "email": "o2@test.com", "password": "Password1", "role": "officer"}
    assert client.post("/api/users", json=body, headers=headers).status_code == 400
    body["department_id"] = 1
    assert client.post("/api/users", json=body, headers=headers).status_code == 201


def test_departments_are_public(client):
    response = client.get("/api/departments")
    assert response.status_code == 200
    assert response.json()[0]["code"] == "roads"


def test_only_citizens_can_submit_reports(client):
    # No photo is sent, so the request would fail validation anyway, but the role
    # check runs first and must answer 403 for officers and admins.
    form = {"latitude": "27.49", "longitude": "77.67", "description": "A pothole"}
    for email in ("officer@test.local", "admin@test.local"):
        response = client.post("/api/reports", data=form, headers=login(client, email))
        assert response.status_code == 403
    assert client.post("/api/reports", data=form).status_code == 401
