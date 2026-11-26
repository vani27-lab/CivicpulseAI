# CivicPulse AI — Module 2: Citizen Reporting Interface

This module sits on top of Module 1. It is a **skeleton** that was checked by reading and static checks only (see section 8). Antigravity should run it, fix what breaks, and test it.

## 1. What a citizen can now do

Sign in as a citizen, press **Start a report**, and send a report made of:

1. **A photo** (JPEG, PNG or WebP, up to 10 MB). Preview shown before sending.
2. **A location.** "Use my current location" captures GPS latitude, longitude and accuracy. The map pin can then be **dragged**, or the map tapped, to fix the spot.
3. **A description**, typed **or spoken** (microphone button).

The whole website can be switched between **English and हिन्दी** with the buttons in the top bar. The choice is remembered, and voice input listens in the chosen language.

**Completion condition from the master README:** a citizen can submit a complaint using an image, location, and text or voice description.

## 2. Upgrading from Module 1

This ZIP contains the **whole project**, so the easiest way is to replace your old `civicpulse-ai` folder with this one (keep your `.env` files if you made any).

- **Docker:** `docker compose up --build -V`
  The `-V` is important: the website container keeps its own copy of `node_modules`, and without `-V` it would not see the two new map packages. Your database is kept, and the new migration runs on start.
- **Without Docker:**
  ```
  cd backend
  alembic upgrade head      # adds the new column (migration 0002)
  cd ../frontend
  npm install               # installs leaflet and react-leaflet
  ```
  `backend/requirements.txt` has no new packages.

## 3. Trying it

1. Open http://localhost:5173, press **Citizen** under "Try a demo account", then **Sign in**.
2. Press **Start a report**.
3. Choose a photo, press **Use my current location** (allow the permission), drag the pin if needed.
4. Type, or press **Speak** and talk. Press **हिन्दी** first to speak Hindi.
5. Press **Send report**. You get a report number.

Browser notes:
- GPS and the microphone work only on **localhost or HTTPS**, not on a plain `http://192.168...` address.
- Voice input works in **Google Chrome and Edge**. Chrome sends the audio to Google to turn it into text. In other browsers the Speak button is replaced by a message, and typing still works.
- If GPS is blocked or unavailable, the person can just tap the map.

## 4. New API

`POST /api/reports` — citizen only. It is **multipart form data** (not JSON) because it carries a file.

| Field | Required | Notes |
|---|---|---|
| `image` | yes | JPEG, PNG or WebP. The real file type is checked from the file contents, not the name. Max `MAX_UPLOAD_MB` (default 10). |
| `latitude` | yes | -90 to 90 |
| `longitude` | yes | -180 to 180 |
| `location_accuracy_m` | no | GPS accuracy in metres. Left out when the pin was placed by hand. |
| `location_source` | no | `gps` (default) or `manual_pin` |
| `description` | yes | 3 to 2000 characters |
| `description_language` | no | `en` (default) or `hi` |
| `used_voice_input` | no | `true` / `false` |

Returns `201` with `report_id`, `complaint_id`, `complaint_status` (`submitted`), the saved values, and `image_url` (like `/uploads/reports/abc.jpg`). Photos are served from `/uploads/...`.

Errors: `400` not a real image / empty, `401` not signed in, `403` not a citizen, `413` photo too large, `422` bad form values.

## 5. What happens when a report is sent

`api/routes/reports.py` → `services/storage.py` (saves the photo, calculates its SHA-256 fingerprint) → `services/report_service.py` (database rows). In ONE transaction it creates:

- a **complaint** — category `unclassified`, status `submitted`, `needs_officer_review = true`, `report_count = 1`
- a **report** — the citizen's description, language, photo, GPS point, accuracy and `location_source`
- a **status_history** row — "Complaint submitted." with the photo (project rule 10)

If saving to the database fails, the saved photo file is deleted again.

**Why "unclassified" and "needs review"?** There is no AI yet (Module 3), so nothing has been classified. This follows rule 7: a missing AI result never blocks a submission. Module 3 will fill in the real category, severity and confidence.

## 6. Database change

One small, additive migration: `alembic/versions/0002_report_location_source.py` adds `reports.location_source` (`gps` or `manual_pin`).

Why: when a citizen moves the pin, the old GPS accuracy no longer describes the final position. This column says which case a row is, so accuracy is never misleading (rule 2). Existing rows default to `gps`.

## 7. Files

**New backend:** `services/storage.py`, `services/report_service.py`, `schemas/report.py`, `api/routes/reports.py`, `alembic/versions/0002_...py`, `tests/test_storage.py`
**Changed backend:** `models/enums.py` (LocationSource), `models/report.py`, `core/config.py` (MAX_UPLOAD_MB), `api/router.py`, `main.py` (serves /uploads), `tests/test_auth_api.py` (one new test), `.env.example`

**New frontend:** `pages/ReportProblem.jsx`, `components/LocationPicker.jsx`, `components/VoiceInputButton.jsx`, `components/LanguageSwitcher.jsx`, `hooks/useSpeechRecognition.js`, `context/LanguageContext.jsx`, `i18n/strings.js`
**Changed frontend:** `App.jsx`, `main.jsx`, `components/Layout.jsx`, `components/ProtectedRoute.jsx`, `pages/Home.jsx`, `Login.jsx`, `Register.jsx`, `NotFound.jsx`, `lib/api.js`, `lib/roles.js`, `package.json`, `vite.config.js`, `tailwind.config.js`

## 8. For Antigravity: please check first

Not run end to end (no packages or database were available). Checked statically: Python syntax and imports, model vs migration columns, frontend imports, and that every translation key exists in both languages.

1. `alembic upgrade head` applies `0002` on top of `0001`.
2. Sign in as the citizen, send a report with a real photo. Check `complaints`, `reports` (with `location_source`), and `status_history` each got one row, and the file exists in `backend/uploads/reports/`.
3. Open the returned `image_url` in the browser (the Vite proxy for `/uploads` should work).
4. Map: the marker icons show, the pin drags, tapping the map moves it, the accuracy circle appears after GPS.
5. Voice: Chrome with the Hindi switch on gives Devanagari text.
6. Try wrong inputs: a `.txt` renamed to `.jpg` (should be 400), a photo over the limit (413), officer/admin calling `/api/reports` (403).
7. `cd backend && pytest`. `test_storage.py` needs no database. The 403 test in `test_auth_api.py` uses SQLite.
8. A real submission needs PostGIS. The SQLite tests cannot cover it.

## 9. Limits (honest list)

- **No AI yet.** Every report becomes an unclassified complaint that needs officer review. **No duplicate merging yet** (Module 4): five reports of one pothole make five complaints for now.
- **Hindi is not translated to English yet.** `description_english` is filled only when the text was in English. Module 3 does translation and real language detection. For now `description_language` is simply the language the person had selected.
- Hindi screen text covers the **citizen screens** (sign in, sign up, home, report). Officer and admin screens stay English until Module 5. Server error messages (for example "Incorrect email or password.") are English.
- Photos are sent **as they are** (no resizing), so a 10 MB limit applies. This also keeps the SHA-256 fingerprint stable for Module 3.
- Uploaded photos are publicly readable by anyone who knows the file address (random names). Fine for the MVP; add access control before real use.
- The map uses the free OpenStreetMap tile server, which is meant for light use. For a real launch, use a tile provider or your own tiles.
- The pin is never checked against a city boundary. Wrong locations are possible.

## 10. Notes for Module 3

- Input to read: `report.image_path` (file under `UPLOAD_DIR`), `report.image_sha256`, `report.description_original`, `report.description_language`.
- Output to write: `complaint.category`, `severity`, `ai_confidence`, `ai_explanation`, `needs_officer_review` (true if confidence < 70%, rule 5), `is_demo_result`, and `report.description_english`.
- Where to call it: in `services/report_service.py`, search for `TODO Module 3`. Save the report **first**, then classify, so a failure never blocks submission.
- Module 4's hooks are marked `TODO Module 4` in the same file.
