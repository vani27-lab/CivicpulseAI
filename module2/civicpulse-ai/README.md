# CivicPulse AI — Module 1: Foundation

> **Update: Module 2 has been added.** See **MODULE2_README.md** for what is new, how to upgrade and how to try it.
> The rest of this file describes Module 1. Where it says that the complaint form, photo upload, GPS, voice or language switcher
> do not exist yet (section 8), Module 2 now provides them. Section 6 lists only the Module 1 API; the new one is in MODULE2_README.md.


This is the **skeleton** of Module 1. It sets up the base the other five modules will build on.
It is **not** a finished app. Antigravity should run it, fix whatever breaks, and test it (see section 9).

## 1. What Module 1 gives you

- **Backend** (Python + FastAPI): login, sign-up, roles, a health check.
- **Database** (PostgreSQL + PostGIS): 5 tables, created by Alembic migrations.
- **Roles:** Citizen, Officer, Admin.
- **Demo data:** 4 departments, 7 demo users, 6 demo complaints.
- **Frontend** (React + Vite + Tailwind): sign in, sign up, and a simple home page for each role.
- **Docker** setup, and instructions for running without Docker.

**Completion condition from the master README:** users can log in with different roles, and the database is initialised with sample records.

## 2. Folder map

```
civicpulse-ai/
├── docker-compose.yml        # starts database + backend + frontend together
├── .env.example              # settings for Docker (optional)
├── db/local_setup.sql        # one-time database setup for the NON-Docker way
├── backend/
│   ├── app/
│   │   ├── main.py           # the FastAPI app starts here
│   │   ├── core/             # config.py (settings), security.py (passwords, tokens), geo.py
│   │   ├── db/               # session.py (connection), base.py, seed.py (demo data)
│   │   ├── models/           # the 5 tables (one file each) + enums.py
│   │   ├── schemas/          # what the API accepts and returns
│   │   ├── api/              # deps.py (who is logged in), router.py, routes/
│   │   └── services/         # empty for now: business logic arrives in modules 2-6
│   ├── alembic/              # database migrations
│   ├── tests/                # automated tests
│   ├── requirements.txt
│   └── .env.example          # settings for the NON-Docker way
└── frontend/
    ├── src/
    │   ├── pages/            # Login, Register, Home, NotFound
    │   ├── components/       # Layout, ProtectedRoute, Field, Alert
    │   ├── context/          # AuthContext (who is signed in)
    │   └── lib/              # api.js (talks to backend), roles.js
    └── package.json
```

## 3. Demo accounts

All demo accounts use the password **`Demo@1234`**. They are fake and exist only for demos.

| Role | Email |
|---|---|
| Admin | admin@civicpulse.demo |
| Officer (Roads) | officer.roads@civicpulse.demo |
| Officer (Sanitation) | officer.sanitation@civicpulse.demo |
| Officer (Electrical) | officer.electrical@civicpulse.demo |
| Officer (Drainage) | officer.drainage@civicpulse.demo |
| Citizen | citizen@civicpulse.demo |
| Citizen (Hindi preference) | citizen.hindi@civicpulse.demo |

The sign-in page also has "Try a demo account" buttons that fill the form for you.

## 4. Option A: run with Docker (easiest)

You need **Docker Desktop**. Then, in the `civicpulse-ai` folder:

```
docker compose up --build
```

Wait until you see the backend say it started. Then open:

- Website: http://localhost:5173
- API documentation (try the API in the browser): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

The database is available on your computer at port **5433** (not 5432), so it will not clash with a PostgreSQL you may already have.

To stop: press `Ctrl + C`. To delete the database and start fresh: `docker compose down -v`.

## 5. Option B: run without Docker (local PostgreSQL)

**Step 1. Install PostgreSQL with PostGIS.** On Windows, run the PostgreSQL installer and, when it finishes, use **Stack Builder** to add **PostGIS** (under "Spatial Extensions"). On macOS: `brew install postgresql postgis`. On Ubuntu: `sudo apt install postgresql postgis`.

**Step 2. Create the database** (once):

```
psql -U postgres -f db/local_setup.sql
```

**Step 3. Start the backend** (Python 3.11 or newer):

```
cd backend
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env        # macOS / Linux: cp .env.example .env
# Open .env and fix the password in DATABASE_URL if yours is not "postgres"
alembic upgrade head          # creates the tables
python -m app.db.seed         # adds the demo data
uvicorn app.main:app --reload
```

**Step 4. Start the website** (new terminal, Node.js 18 or newer):

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## 6. API in Module 1

All routes start with `/api`.

| Method | Route | Who can use it | What it does |
|---|---|---|---|
| GET | `/health` | everyone | Shows server, database and PostGIS status |
| POST | `/auth/register` | everyone | Creates a **citizen** account and signs in |
| POST | `/auth/login` | everyone | Signs in (JSON: `email`, `password`) |
| POST | `/auth/token` | everyone | Same, in form format (used by the Authorize button on `/docs`) |
| GET | `/auth/me` | signed in | Returns the signed-in user |
| GET | `/departments` | everyone | Lists the four departments |
| GET | `/users` | admin | Lists all users |
| POST | `/users` | admin | Creates an officer or admin (officers need `department_id`) |

## 7. Database

One database: **PostgreSQL + PostGIS**. Five tables:

| Table | Purpose |
|---|---|
| `users` | Accounts. `role` is `citizen`, `officer` or `admin`. Officers have a `department_id`. |
| `departments` | Roads, Sanitation, Electrical, Drainage. |
| `complaints` | **One real-world problem.** Category, location, AI result, priority, status. |
| `reports` | **One citizen's submission.** Several reports can belong to one complaint (this is how duplicate merging works). |
| `status_history` | One row for every status change: time, who, status, optional photograph. |

Choices made, so later modules stay consistent:

- **Complaint vs report.** The complaint is the problem; each citizen's submission is a report. To split a wrongly merged report, Module 4/5 just points that report to a new complaint.
- **Location is stored twice on purpose.** `latitude` and `longitude` (easy for the website), plus `location` (a PostGIS point, used for the 50-metre search). `location_accuracy_m` is stored with them (rule 2).
- **PostGIS wants longitude first.** Always create points with `app/core/geo.py → make_point(latitude, longitude)`.
- **CLIP embeddings** are stored as a plain list of numbers (`image_embedding`, a PostgreSQL array). No second database and no extra extension. The 50-metre search narrows the candidates first, so comparing the lists in Python is fine at MVP size.
- **Statuses and categories** are plain text columns with fixed allowed values, defined in `app/models/enums.py`. Changing the list later does not need a database enum migration.
- Fields for later modules (`severity`, `ai_confidence`, `needs_officer_review`, `is_demo_result`, `priority_*`, `duplicate_status`, `image_similarity`) already exist and are empty or demo-filled until those modules are built.

## 8. What Module 1 does NOT do (on purpose)

No complaint form, photo upload, GPS, voice, language switcher, AI, duplicate detection, real priority calculation, routing, officer dashboard or tracking page. These belong to Modules 2 to 6.

The demo complaints are fake rows from `app/db/seed.py`. Their priority numbers use the README formula, but only as sample data. Module 4 will provide the real calculation.

## 9. For Antigravity: please check first

This skeleton was written without being able to install packages or start a database, so **it has not been run end to end**. What *was* checked: every Python file parses, every `from app... import ...` points to something that exists, and the model columns match the migration columns for all five tables.

Please do these in order and fix what breaks:

1. `docker compose up --build`: do all three containers start? Does `alembic upgrade head` succeed on `postgis/postgis:16-3.4`?
2. `GET /api/health` should say `"postgis": "3.4 ..."`.
3. `cd backend && pytest`: the tests use SQLite and only the `users` and `departments` tables (the others need PostGIS).
4. Log in with each demo account on the website. Each role should see its own home page. The admin should see a list of 7 people.
5. Check the seed ran: 4 departments, 7 users, 6 complaints, with `status_history` rows.
6. Confirm the PostGIS indexes exist: `\d complaints` should show `ix_complaints_location ... USING gist`.
7. Pin or update package versions if any fail to install.

## 10. Rules for the next modules

- Never change the five tables without a new Alembic migration (`alembic revision -m "..."`).
- Every status change must write a `status_history` row.
- Add new API routes in `backend/app/api/routes/` and register them in `api/router.py`; put business logic in `services/`.
- Protect routes with `require_roles(...)` from `app/api/deps.py`.
- Frontend: keep using `src/lib/api.js` for all calls and `AuthContext` for the signed-in user.
- Module 2 will add the English/Hindi switcher. Until then all screen text is English, and the user's `preferred_language` is already stored.
- Frontend style: calm, plain, uncluttered. Large readable text, one accent colour, labels above every input.

## 11. Assumptions

- Python 3.11+ (Docker uses 3.12). Node 18+ (Docker uses 20).
- The demo password and `JWT_SECRET_KEY` default are for local use only. Change both before any real deployment.
- Registration is open for citizens only. Officers and admins are created by an admin.
- Demo complaint locations are sample coordinates; change them in `seed.py` if you want them somewhere else.
