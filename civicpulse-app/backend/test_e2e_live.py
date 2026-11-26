import httpx
import sys

BASE_URL = "http://127.0.0.1:8000"
JPEG_DUMMY = b"\xff\xd8\xff\xe0" + b"\x00" * 300

def run_e2e():
    client = httpx.Client(base_url=BASE_URL, timeout=20.0)

    print("==================================================")
    print("STEP 1: Checking Backend Health")
    print("==================================================")
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    health = r.json()
    print("Health Status:", health)
    assert health["status"] == "ok"
    assert health["database"] == "connected"

    print("\n==================================================")
    print("STEP 2: Citizen Authentication")
    print("==================================================")
    citizen_email = "citizen@civicpulse.gov"
    citizen_pass = "Citizen@123"
    r = client.post("/api/auth/login", json={"email": citizen_email, "password": citizen_pass})
    if r.status_code != 200:
        print("Creating citizen account...")
        client.post("/api/auth/register", json={
            "email": citizen_email,
            "password": citizen_pass,
            "full_name": "Citizen Ramesh"
        })
        r = client.post("/api/auth/login", json={"email": citizen_email, "password": citizen_pass})
    
    assert r.status_code == 200, f"Citizen login failed: {r.text}"
    citizen_token = r.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("Citizen authenticated successfully.")

    print("\n==================================================")
    print("STEP 3: Submitting Citizen Problem Report Near Hospital")
    print("Coordinates: 27.603397, 77.595745 (Mathura Hospital Area)")
    print("==================================================")
    files = {
        "image": ("pothole.jpg", JPEG_DUMMY, "image/jpeg")
    }
    data = {
        "latitude": 27.603397,
        "longitude": 77.595745,
        "description": "Massive deep road rupture and crater blocking ambulance entrance gate.",
        "description_language": "en",
        "location_source": "gps",
        "used_voice_input": "false"
    }

    r = client.post("/api/reports", data=data, files=files, headers=citizen_headers)
    assert r.status_code == 201, f"Report submission failed: {r.status_code} - {r.text}"
    report_res = r.json()
    report_id = report_res["report_id"]
    complaint_id = report_res["complaint_id"]
    print(f"Report Submitted! Report ID: {report_id}, Complaint ID: {complaint_id}")

    print("\n==================================================")
    print("STEP 4: Citizen Tracking & Priority Verification")
    print(f"Endpoint: GET /api/complaints/{complaint_id}")
    print("==================================================")
    r = client.get(f"/api/complaints/{complaint_id}", headers=citizen_headers)
    assert r.status_code == 200, f"Citizen tracking failed: {r.text}"
    c_track = r.json()
    print("Citizen Complaint State:")
    print(f"  - Issue Type: {c_track.get('issue_type')}")
    print(f"  - Status: {c_track.get('status')}")
    print(f"  - Priority Band: {c_track.get('priority_band')}")
    print(f"  - Emergency Flag: {c_track.get('is_emergency')}")
    print(f"  - Nearest Facility: {c_track.get('nearest_facility_name')} ({c_track.get('nearest_facility_distance_m')}m)")
    print(f"  - Urgency Notice: {c_track.get('citizen_urgency_reason')}")

    assert c_track["priority_band"] == "CRITICAL", f"Expected CRITICAL, got {c_track.get('priority_band')}"
    assert c_track["is_emergency"] is True, "Emergency escalation failed"
    assert c_track["nearest_facility_name"] is not None
    assert c_track["citizen_urgency_reason"] is not None

    print("\n==================================================")
    print("STEP 5: Officer Authentication & Inspection")
    print("==================================================")
    r = client.post("/api/auth/login", json={"email": "officer@civicpulse.gov", "password": "Officer@123"})
    assert r.status_code == 200, f"Officer login failed: {r.text}"
    officer_token = r.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print("Officer authenticated successfully.")

    r = client.get(f"/officer/complaints/{complaint_id}", headers=officer_headers)
    assert r.status_code == 200, f"Officer get complaint failed: {r.text}"
    c_officer = r.json()
    print("Officer Detailed View:")
    print(f"  - Priority Band: {c_officer.get('priority_band')}")
    print(f"  - Priority Score: {c_officer.get('priority_score')}/100")
    print(f"  - Emergency Flag: {c_officer.get('is_emergency')}")
    print(f"  - Nearest Facility: {c_officer.get('nearest_facility')}")
    print(f"  - Nearby Critical Facilities: {len(c_officer.get('nearby_facilities', []))} found")
    print(f"  - Status: {c_officer.get('status')}")

    assert c_officer["priority_band"] == "CRITICAL"
    assert c_officer["is_emergency"] is True
    assert len(c_officer.get("nearby_facilities", [])) >= 1

    print("\n==================================================")
    print("STEP 6: Officer Action - Dispatching Team (IN_PROGRESS)")
    print("==================================================")
    r = client.patch(
        f"/officer/complaints/{complaint_id}/status",
        json={"status": "IN_PROGRESS", "remarks": "High-priority road repair squad dispatched immediately to hospital access point."},
        headers=officer_headers
    )
    assert r.status_code == 200, f"Status update to IN_PROGRESS failed: {r.text}"
    print("Complaint updated to IN_PROGRESS.")

    print("\n==================================================")
    print("STEP 7: Officer Action - Resolving Issue (RESOLVED)")
    print("==================================================")
    r = client.patch(
        f"/officer/complaints/{complaint_id}/status",
        json={"status": "RESOLVED", "remarks": "Road surface reconstructed and hot-mix asphalt laid. Ambulance corridor 100% restored."},
        headers=officer_headers
    )
    assert r.status_code == 200, f"Status update to RESOLVED failed: {r.text}"
    print("Complaint updated to RESOLVED.")

    print("\n==================================================")
    print("STEP 8: Citizen Verification & History")
    print("==================================================")
    r = client.get(f"/api/complaints/{complaint_id}", headers=citizen_headers)
    assert r.status_code == 200
    final_c = r.json()
    print("Citizen Verified Final Status:", final_c["status"])
    assert final_c["status"] == "resolved"

    r_hist = client.get(f"/api/complaints/{complaint_id}/history", headers=citizen_headers)
    assert r_hist.status_code == 200
    hist = r_hist.json().get("history", [])
    print(f"Audit Trail Steps ({len(hist)}):")
    for step in hist:
        print(f"  - [{step.get('created_at')}] {step.get('new_status')}: {step.get('comment')}")

    print("\n==================================================")
    print("STEP 9: Citizen Resolution Feedback")
    print("==================================================")
    r_fb = client.post(
        f"/api/complaints/{complaint_id}/feedback",
        json={"rating": 5, "comment": "Outstanding emergency response! The road was fixed within hours."},
        headers=citizen_headers
    )
    if r_fb.status_code == 200:
        print("Citizen feedback submitted successfully (5 stars).")
    else:
        print(f"Citizen feedback status: {r_fb.status_code}")

    print("\n=================================================================")
    print(">>> 100% END-TO-END VERIFICATION COMPLETED AND VALIDATED! <<<")
    print("=================================================================")

if __name__ == "__main__":
    run_e2e()
