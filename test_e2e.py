"""End-to-End Test for CivicPulse AI MVP.

Workflow:
Citizen Login -> Submit complaint -> AI Classification & Priority -> Officer Dashboard -> Status update -> Citizen tracking -> Resolution with After-Photo
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "civicpulse-app" / "backend"))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def run_test():
    print("=== Step 1: Health Check ===")
    res = client.get("/api/health")
    assert res.status_code == 200, res.text
    print("Health OK:", res.json())

    print("\n=== Step 2: Citizen Login ===")
    res = client.post("/api/auth/login", json={"email": "citizen@civicpulse.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    citizen_token = res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    print("Citizen logged in. User:", res.json()["user"]["full_name"])

    print("\n=== Step 3: Citizen Submits Complaint with Image ===")
    dummy_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
    )
    files = {"image": ("pothole.jpg", dummy_jpeg, "image/jpeg")}
    data = {
        "description": "Dangerous deep pothole on MG Road causing severe traffic hazard",
        "language": "en",
        "latitude": 27.4925,
        "longitude": 77.6735,
        "location_accuracy_m": 5.0,
        "location_source": "gps",
        "used_voice_input": "false",
    }
    res = client.post("/api/reports", files=files, data=data, headers=citizen_headers)
    assert res.status_code == 201, res.text
    rep_data = res.json()
    complaint_id = rep_data["complaint_id"]
    print(f"Report submitted! ID: {rep_data['report_id']}, Complaint ID: {complaint_id}, Status: {rep_data['complaint_status']}")

    print("\n=== Step 4: Officer Login ===")
    res = client.post("/api/auth/login", json={"email": "officer.roads@civicpulse.demo", "password": "Demo@1234"})
    assert res.status_code == 200, res.text
    officer_token = res.json()["access_token"]
    officer_headers = {"Authorization": f"Bearer {officer_token}"}
    print("Officer logged in. User:", res.json()["user"]["full_name"])

    print("\n=== Step 5: Officer Views Dashboard Stats & List ===")
    res = client.get("/officer/dashboard/stats", headers=officer_headers)
    assert res.status_code == 200, res.text
    print("Officer Stats:", res.json())

    res = client.get("/officer/complaints", headers=officer_headers)
    assert res.status_code == 200, res.text
    complaints = res.json()["items"]
    print(f"Total Complaints listed for officer: {len(complaints)}")

    res = client.get(f"/officer/complaints/{complaint_id}", headers=officer_headers)
    assert res.status_code == 200, res.text
    detail = res.json()
    print("Complaint Detail retrieved:")
    print(f"  Issue: {detail['issue_type']}, Status: {detail['status']}, Priority: {detail['priority']['band']} ({detail['priority']['score']}/100)")
    print(f"  Reasons: {detail['priority']['reasons']}")

    print("\n=== Step 6: Officer Updates Status to 'in_progress' ===")
    res = client.patch(
        f"/complaints/{complaint_id}/status",
        headers=officer_headers,
        data={"new_status": "in_progress", "comment": "Road repair team dispatched with asphalt equipment."},
    )
    assert res.status_code == 200, res.text
    print("Status updated successfully:", res.json()["new_status"])

    print("\n=== Step 7: Officer Resolves Complaint with After-Photo ===")
    after_files = {"after_photo": ("repaired.jpg", dummy_jpeg, "image/jpeg")}
    res = client.patch(
        f"/complaints/{complaint_id}/status",
        headers=officer_headers,
        data={"new_status": "resolved", "comment": "Pothole filled with hot-mix asphalt and compacted."},
        files=after_files,
    )
    assert res.status_code == 200, res.text
    print("Complaint resolved! After photo:", res.json()["after_photo_url"])

    print("\n=== Step 8: Citizen Checks Tracking & Notifications ===")
    res = client.get("/complaints/mine", headers=citizen_headers)
    assert res.status_code == 200, res.text
    my_complaints = res.json()["items"]
    my_c = next(c for c in my_complaints if c["id"] == str(complaint_id))
    print(f"Complaint {complaint_id} status in citizen tracking view is: {my_c['status']}")
    assert my_c["status"] == "resolved", f"Expected resolved, got {my_c['status']}"

    res = client.get(f"/complaints/{complaint_id}/history", headers=citizen_headers)
    assert res.status_code == 200, res.text
    print("Citizen History Timeline:")
    for h in res.json()["items"]:
        print(f"  - [{h['created_at']}] {h['old_status']} -> {h['new_status']}: {h['comment']}")

    res = client.get("/notifications", headers=citizen_headers)
    assert res.status_code == 200, res.text
    print(f"Citizen Notifications count: {len(res.json()['items'])}")

    print("\n=======================================================")
    print("ALL 8 END-TO-END DEMO WORKFLOW STEPS (INCLUDING RESOLUTION) PASSED!")
    print("=======================================================")

if __name__ == "__main__":
    run_test()
