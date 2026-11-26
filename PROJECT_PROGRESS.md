# CivicPulse AI — Final Project Handover & Progress Report

**Document Date:** November 26, 2026  
**Status:** CODE FREEZE — FINAL HANDOVER FOR MANUAL DEPLOYMENT  
**Git Repository:** `https://github.com/vani27-lab/CivicpulseAI.git`  
**Current Branch:** `main` (Working tree clean, all commits pushed)

---

## 1. Verified Live Services & Local URLs

Both backend and frontend services have been verified and are active:

| Service | Verified Local URL | Status | Verified Response |
|---|---|---|---|
| **Frontend Web Application** | `http://localhost:5173` | **ONLINE** | `HTTP/1.1 200 OK` (Vite dev server) |
| **Backend REST API** | `http://localhost:8000` | **ONLINE** | `{"status":"ok","database":"connected","postgis":"not installed"}` |
| **Interactive API Documentation** | `http://localhost:8000/docs` | **ONLINE** | Swagger UI / OpenAPI 3.1 schema |

---

## 2. Working Demo Login Credentials

All demo accounts exist in the SQLite database and are verified working with password **`Demo@1234`**:

| Role | Email | Password | Primary Interface / Features |
|---|---|---|---|
| **Roads Officer** | `officer.roads@civicpulse.demo` | `Demo@1234` | Officer Dashboard (`/officer/dashboard`), Complaint Detail, Status Management |
| **Sanitation Officer** | `officer.sanitation@civicpulse.demo` | `Demo@1234` | Sanitation Department Queue & Resolution |
| **Electrical Officer** | `officer.electrical@civicpulse.demo` | `Demo@1234` | Electrical & Streetlight Queue |
| **Drainage Officer** | `officer.drainage@civicpulse.demo` | `Demo@1234` | Drainage & Waterlogging Queue |
| **Citizen (English)** | `citizen@civicpulse.demo` | `Demo@1234` | Report Problem (`/report`), My Complaints & Tracking (`/citizen/complaints`) |
| **Citizen (Hindi)** | `citizen.hindi@civicpulse.demo` | `Demo@1234` | Multilingual citizen flow |
| **System Admin** | `admin@civicpulse.demo` | `Demo@1234` | User management & department administration |

---

## 3. Technology Stack & Folder Structure

### Locations
- **Unified Application Root:** `civicpulse-app/`
- **Frontend Codebase:** `civicpulse-app/frontend/`
- **Backend Codebase:** `civicpulse-app/backend/`
- **Original Source Modules:** Preserved in `module1/` through `module6/` and root `.zip` archives.

### Tech Stack
- **Frontend:** React 18, Vite 5, Tailwind CSS 3, React Router v6, Leaflet / React-Leaflet, Heroicons, Lucide-React. Modern Industrial Editorial design (`#F4F0E9` background, `#782F32` burgundy accent).
- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, Passlib (bcrypt), PyJWT, GeoAlchemy2, httpx.
- **Database Engine:** SQLite (local zero-dependency fallback) / PostgreSQL 16 + PostGIS 3.4 (production-ready).

---

## 4. Build and Startup Commands

### Backend (`civicpulse-app/backend`)
```bash
# Install dependencies
pip install -r requirements.txt

# Start development / production server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run unit tests
python -m pytest tests/ -v
```

### Frontend (`civicpulse-app/frontend`)
```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev -- --host 0.0.0.0

# Build for production
npm run build
```

---

## 5. Required Environment Variables

### Backend (`civicpulse-app/backend/.env`)
```ini
APP_NAME=CivicPulse AI
ENVIRONMENT=development
DATABASE_URL=sqlite:///./civicpulse.db
# For production PostgreSQL + PostGIS:
# DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/civicpulse
JWT_SECRET_KEY=dev-secret-change-me-at-least-32-chars-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
UPLOAD_DIR=uploads
MAX_UPLOAD_MB=10
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SEED_DEMO_DATA=true
DEMO_PASSWORD=Demo@1234
AI_VISION_API_KEY=
```

### Frontend (`civicpulse-app/frontend/.env`)
```ini
# Optional: In development, vite.config.js automatically proxies /api to http://localhost:8000
VITE_API_BASE_URL=
```

---

## 6. Detailed Feature Status Matrix

### Completed Features (Verified 100%)
- [x] **Authentication & RBAC:** Citizen self-registration, role-based JWT authentication (`citizen`, `officer`, `admin`), password hashing with bcrypt.
- [x] **Citizen Problem Submission:** Photo attachment validation, draggable Leaflet map pin, browser geolocation auto-detect, bilingual UI (English / Hindi), speech-to-text voice input.
- [x] **Dynamic Routing:** Automatic assignment to 4 municipal departments (Roads, Sanitation, Electrical, Drainage) based on category classification.
- [x] **Geo-Aware Priority Engine:** 5-factor scoring model (Severity 30%, Proximity 25%, Impact 20%, Duplicates 15%, Urgency 10%). 4 calibrated priority bands: `CRITICAL` (75–100), `HIGH` (50–74), `MEDIUM` (30–49), `LOW` (0–29).
- [x] **Emergency Escalation:** Severe issues within 50m of critical emergency facilities (e.g. hospital entrance craters) automatically escalate to `CRITICAL` with score $\ge 82.0$.
- [x] **Explainable Citizen Notices:** Plain-language urgency reason shown to citizens without exposing raw mathematical scoring.
- [x] **Officer Dashboard:** Department-scoped KPI summary cards, filterable complaint list (including `CRITICAL`), interactive Leaflet map with colored priority markers, and nearest facility popups.
- [x] **Status Progression & Audit Trail:** Validated status transitions (`submitted` → `assigned` → `in_progress` → `resolved`), status history logging with comments and officer timestamps.
- [x] **Citizen Tracking & Transparency:** Step-by-step progress timeline, before/after photo evidence display, and star-rating feedback submission.

### Partially Implemented Features
- [!] **External Vision AI (`classify_complaint`):** Ready for Google Cloud Vision API key. When API key is omitted, system transparently executes bilingual keyword heuristics (`pothole`, `सड़क`, `गड्ढा`, `garbage`, `streetlight`, `drainage`).
- [!] **Overpass OpenStreetMap Live Facility Query:** Includes local landmark seeds and indexed database facility cache. Network queries execute gracefully when online; system falls back to seeded infrastructure landmarks without blocking or faking responses.
- [!] **Duplicate Report Merging:** Haversine 50-meter spatial proximity grouping functional. Advanced split-panel UI exists; officer split action endpoint is wired.

### Features Not Implemented
- [-] SMS / WhatsApp notifications (mock in-app notification bell used).
- [-] External cloud object storage (AWS S3 / Cloudinary) — all photos are stored on local persistent disk.
- [-] Automated push notification webhooks for external contractors.

---

## 7. Known Bugs, Storage Implementation & Limitations

1. **Database Mode (SQLite vs PostGIS):**
   - SQLite is used locally (`civicpulse.db`). Spatial queries use Haversine mathematical formulas in Python.
   - For PostgreSQL + PostGIS, the codebase includes GeoAlchemy2 models (`Geometry("POINT", srid=4326)`). When migrating to PostgreSQL, ensure the `postgis` extension is activated (`CREATE EXTENSION postgis;`).
2. **Image Storage Pipeline:**
   - Uploaded photos are stored on disk in `civicpulse-app/backend/uploads/` (categorized under `reports/` and `resolutions/`).
   - Photos are served via FastAPI static mounts at `/uploads` and `/media`.
   - In containerized deployments (Docker / Render), `uploads/` must be mounted to a persistent volume or ephemeral dyno restarts will wipe newly uploaded photos (pre-seeded demo complaints will remain).
3. **Pydantic Email Validation:**
   - Field `email` uses length-validated string checking to allow local demo domains (`.demo`, `.local`) during testing and evaluation.

---

## 8. Git Commit & Push Status

- **Status:** All code changes staged, committed, and pushed to remote.
- **Target Remote:** `origin` (`https://github.com/vani27-lab/CivicpulseAI.git`)
- **Target Branch:** `main`
- **Latest Commit:** `feat(final): complete geo-aware priority engine, verified demo workflow, and production readiness`
- **Working Tree:** Clean (no untracked or uncommitted files).
