import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

print("1. Testing Citizen Login (citizen@civicpulse.demo / Demo@1234)...")
r = client.post("/api/auth/login", json={"email": "citizen@civicpulse.demo", "password": "Demo@1234"})
assert r.status_code == 200, f"Citizen login failed: {r.text}"
citizen_token = r.json()["access_token"]
print(" Citizen login SUCCESS. Token acquired.")

print("2. Submitting Citizen Complaint...")
JPEG_DUMMY = b"\xff\xd8\xff\xe0" + b"\x00" * 300
files = {"image": ("test_pothole.jpg", JPEG_DUMMY, "image/jpeg")}
data = {
    "latitude": 27.603397,
    "longitude": 77.595745,
    "description": "Hazardous road crater disrupting traffic near hospital.",
    "description_language": "en",
    "location_source": "gps",
}
r = client.post(
    "/api/reports",
    data=data,
    files=files,
    headers={"Authorization": f"Bearer {citizen_token}"}
)
assert r.status_code == 201, f"Report submission failed: {r.status_code} {r.text}"
res = r.json()
complaint_id = res["complaint_id"]
print(f" Citizen complaint submitted SUCCESS! Complaint ID: {complaint_id}")

print("3. Testing Officer Login (officer.roads@civicpulse.demo / Demo@1234)...")
r = client.post("/api/auth/login", json={"email": "officer.roads@civicpulse.demo", "password": "Demo@1234"})
assert r.status_code == 200, f"Officer login failed: {r.text}"
officer_token = r.json()["access_token"]
print(" Officer login SUCCESS. Token acquired.")

print("4. Officer Viewing Complaints List...")
r = client.get("/officer/complaints", headers={"Authorization": f"Bearer {officer_token}"})
assert r.status_code == 200, f"Officer fetch failed: {r.text}"
complaints_list = r.json().get("items", [])
print(f" Officer dashboard loaded SUCCESS! Found {len(complaints_list)} complaints.")

print("5. Officer Viewing Complaint Detail...")
r = client.get(f"/officer/complaints/{complaint_id}", headers={"Authorization": f"Bearer {officer_token}"})
assert r.status_code == 200, f"Officer detail failed: {r.text}"
detail = r.json()
print(f" Officer detail view SUCCESS! ID={detail['id']}, Status={detail['status']}, Priority={detail['priority']['band']}, Facility={detail['priority']['nearest_facility_name']}")

print("6. Testing Admin Login (admin@civicpulse.demo / Demo@1234)...")
r = client.post("/api/auth/login", json={"email": "admin@civicpulse.demo", "password": "Demo@1234"})
assert r.status_code == 200, f"Admin login failed: {r.text}"
print(" Admin login SUCCESS.")

print("\n========================================================")
print(">>> ALL DEMO WORKFLOWS VERIFIED ON LOCALHOST 100% <<<")
print("========================================================")
