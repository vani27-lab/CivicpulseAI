import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.anyio
async def test_full_civicpulse_e2e_workflow(client: AsyncClient, test_user):
    """
    End-to-End Workflow Verification:
    1. Authenticate citizen
    2. Submit emergency-severity complaint near critical hospital
    3. Verify geo-aware priority engine assigns CRITICAL priority and emergency flag
    4. Verify citizen tracking endpoint surfaces urgency notice and facility
    5. Authenticate officer
    6. Officer queries complaint details including geospatial analysis & nearby facilities
    7. Officer updates status to IN_PROGRESS and then RESOLVED
    8. Citizen tracking reflects resolution
    """
    # 1. Citizen login
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "citizen@test.local", "password": "Password123!"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    citizen_token = login_resp.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 2. Citizen submits complaint near Lifeline Emergency Clinic (Mathura: 27.603397, 77.595745)
    submit_payload = {
        "title": "Severe road crater blocking emergency ambulance access",
        "description": "Massive deep crater right at the main hospital entrance. Ambulances are getting stranded.",
        "category": "road",
        "severity": "HIGH",
        "latitude": 27.603397,
        "longitude": 77.595745,
        "address": "Opposite Lifeline Emergency Clinic, Mathura",
        "landmark": "Lifeline Emergency Clinic"
    }

    submit_resp = await client.post(
        "/api/complaints/submit",
        json=submit_payload,
        headers=citizen_headers
    )
    assert submit_resp.status_code == 201, f"Complaint submission failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    complaint_id = submit_data["id"]
    tracking_id = submit_data["tracking_id"]

    assert submit_data["is_emergency"] is True, "Emergency escalation should trigger for severe road block near hospital"
    assert submit_data["priority"] == "critical", f"Expected critical priority, got {submit_data['priority']}"
    assert submit_data["nearest_facility_name"] is not None
    assert "Lifeline" in submit_data["nearest_facility_name"] or "Hospital" in submit_data["nearest_facility_name"] or "Clinic" in submit_data["nearest_facility_name"]

    # 3. Citizen tracking
    track_resp = await client.get(f"/api/v1/tracking/{tracking_id}")
    assert track_resp.status_code == 200, f"Tracking failed: {track_resp.text}"
    track_data = track_resp.json()
    assert track_data["tracking_id"] == tracking_id
    assert track_data["priority"] == "CRITICAL"
    assert track_data["is_emergency"] is True
    assert track_data["citizen_urgency_reason"] is not None
    assert len(track_data["citizen_urgency_reason"]) > 0

    # 4. Officer login
    officer_login = await client.post(
        "/api/auth/login",
        json={"email": "officer@civicpulse.gov", "password": "Officer@123"}
    )
    # If default officer is not in test DB fixture, officer can be authenticated with officer role
    # In conftest test_officer fixture provides an officer if needed, or let's check
    if officer_login.status_code != 200:
        # Register an officer or use test_officer fixture
        reg_officer = await client.post(
            "/api/auth/register",
            json={"email": "officer.e2e@civicpulse.gov", "password": "Password123!", "full_name": "E2E Officer"}
        )
        assert reg_officer.status_code == 201
        # login
        officer_login = await client.post(
            "/api/auth/login",
            json={"email": "officer.e2e@civicpulse.gov", "password": "Password123!"}
        )

    officer_token = officer_login.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    # 5. Officer inspects complaint detail
    detail_resp = await client.get(
        f"/officer/complaints/{complaint_id}",
        headers=officer_headers
    )
    assert detail_resp.status_code == 200, f"Officer detail fetch failed: {detail_resp.text}"
    detail_data = detail_resp.json()
    assert detail_data["id"] == complaint_id
    assert detail_data["priority_band"] == "CRITICAL"
    assert detail_data["is_emergency"] is True
    assert detail_data["nearest_facility"] is not None
    assert len(detail_data.get("nearby_facilities", [])) >= 1
    assert detail_data["status"] == "SUBMITTED"

    # 6. Officer updates status to IN_PROGRESS
    status_resp = await client.patch(
        f"/officer/complaints/{complaint_id}/status",
        json={"status": "IN_PROGRESS", "remarks": "Road crew dispatched to clear hospital access route."},
        headers=officer_headers
    )
    assert status_resp.status_code == 200, f"Status update failed: {status_resp.text}"
    assert status_resp.json()["status"] == "IN_PROGRESS"

    # 7. Officer resolves complaint
    resolve_resp = await client.patch(
        f"/officer/complaints/{complaint_id}/status",
        json={"status": "RESOLVED", "remarks": "Asphalt patch completed. Ambulance route fully restored."},
        headers=officer_headers
    )
    assert resolve_resp.status_code == 200, f"Resolution update failed: {resolve_resp.text}"
    assert resolve_resp.json()["status"] == "RESOLVED"

    # 8. Citizen verifies resolution in tracking
    track_resp_final = await client.get(f"/api/v1/tracking/{tracking_id}")
    assert track_resp_final.status_code == 200
    assert track_resp_final.json()["status"] == "RESOLVED"
    print("E2E Workflow test passed successfully!")
