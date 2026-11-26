# CivicPulse AI

> **Intelligent Civic Issue Reporting, Prioritisation, and Resolution Platform**

CivicPulse AI is an end-to-end civic complaint management platform that empowers citizens to report public infrastructure issues (potholes, garbage, broken streetlights, drainage) with photos and GPS, applies AI intelligence to classify and prioritise complaints, and equips municipal officers with an actionable dashboard to manage workflows and record resolution evidence.

---

## 🚀 Key Features (Verified MVP)

- **Citizen Reporting**: Report issues with photo upload, drag-and-drop map pin / device GPS capture, description (English & Hindi support), and voice-to-text.
- **AI Classification**: Categorises reported issues into municipal departments (`Roads`, `Sanitation`, `Electrical`, `Drainage`), assigns severity (1–4), and flags uncertain reports for review.
- **Explainable Priority Engine**: Ranks complaints based on severity, report velocity, pending age, and nearby critical infrastructure (schools, hospitals, main roads).
- **Officer Dashboard**: Real-time KPI statistics, sortable/filterable complaint table, spatial map, and density heatmap.
- **Status Progression & Evidence**: Forward status management (`submitted` → `assigned` → `in_progress` → `resolved`) with mandatory after-photo resolution evidence.
- **Citizen Live Tracking & Timeline**: Citizens track their own complaints through a live timeline history with translated officer updates and in-app notifications.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn, PyJWT, Passlib/Bcrypt
- **Frontend**: React 18, Vite, Tailwind CSS, Leaflet & React-Leaflet, Leaflet.heat
- **Database**: PostgreSQL + PostGIS (with zero-dependency transparent SQLite fallback for quick local evaluation)

---

## ⚡ Quick Start (Run in 2 Minutes)

### 1. Prerequisites
- Python 3.11 or newer
- Node.js 18 or newer and npm

### 2. Automated 1-Click Launch (Windows)
Double-click or run:
```cmd
start_demo.bat
```
This automatically launches both the FastAPI backend on port 8000 and the Vite frontend on port 5173.

---

### 3. Manual Launch

#### Backend:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
cd civicpulse-app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

#### Frontend:
```bash
# 1. Install dependencies & start dev server
cd civicpulse-app/frontend
npm install
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Demo Accounts

All demo accounts use the standard password: **`Demo@1234`**

| Role | Email | Capabilities |
|---|---|---|
| **Citizen** | `citizen@civicpulse.demo` | Submit complaints (`/report`), view tracking & timeline (`/citizen/complaints`) |
| **Citizen (Hindi)** | `citizen.hindi@civicpulse.demo` | Bilingual citizen reporting and Hindi interface |
| **Officer (Roads)** | `officer.roads@civicpulse.demo` | Roads department review, priority triage, status updates (`/officer`) |
| **Officer (Sanitation)** | `officer.sanitation@civicpulse.demo` | Sanitation department complaint triage |
| **Officer (Electrical)** | `officer.electrical@civicpulse.demo` | Streetlight & electrical issue triage |
| **Officer (Drainage)** | `officer.drainage@civicpulse.demo` | Drainage & waterlogging triage |
| **Admin** | `admin@civicpulse.demo` | User management & administrative overrides |

---

## 🧪 Automated Verification Test

The repository includes a complete 8-step end-to-end integration test verifying the entire workflow:
```bash
python test_e2e.py
```

### Verified Test Flow:
1. `GET /api/health` -> System health & database connectivity
2. `POST /api/auth/login` -> Citizen authentication
3. `POST /api/reports` -> Citizen photo upload, GPS, and description
4. AI classification, department routing, and explainable priority score calculation
5. `POST /api/auth/login` -> Officer authentication
6. `GET /officer/dashboard/stats` & `GET /officer/complaints/{id}` -> Officer triage
7. `PATCH /complaints/{id}/status` -> Update to `in_progress`, then `resolved` with after-photo
8. `GET /complaints/mine` & `/notifications` -> Citizen live tracking & timeline verification

---

## 📁 Repository Structure

```
CivicPulse-AI/
├── civicpulse-app/               # Unified Production Application
│   ├── backend/                  # FastAPI Application
│   │   ├── app/
│   │   │   ├── api/              # Auth, users, departments, reports routes
│   │   │   ├── core/             # Config, security, geo utils
│   │   │   ├── db/               # Session management & seed data
│   │   │   ├── models/           # SQLAlchemy database models
│   │   │   ├── modules/          # Integrated AI engine & citizen tracking
│   │   │   └── officer/          # Officer dashboard API, status workflow & queries
│   │   ├── uploads/              # Uploaded photographs storage
│   │   └── civicpulse.db         # Pre-seeded SQLite database
│   └── frontend/                 # React + Vite Frontend
│       ├── src/
│       │   ├── components/       # Layout, map picker, voice button, alerts
│       │   ├── context/          # Auth and Language contexts
│       │   ├── modules/citizen/  # Citizen portal, tracking & notification bell
│       │   ├── officer/          # Officer dashboard, map view & complaint details
│       │   └── pages/            # Login, register, home, submit report
│       └── vite.config.js        # Reverse proxy config for /api, /officer, /media
├── module1/ .. module6/          # Preserved isolated module extracts
├── test_e2e.py                   # Automated 8-step integration test suite
├── start_demo.bat                # 1-click application runner
├── start_backend.bat             # Backend runner
├── start_frontend.bat            # Frontend runner
├── PROJECT_PROGRESS.md           # Implementation audit & milestone tracker
├── requirements.txt              # Backend dependencies
└── package.json                  # Frontend dependencies
```

---

## 📄 License
Internal Evaluation / CivicPulse AI Project.
