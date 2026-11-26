# CivicPulse AI - Module 5: Officer Dashboard

Officer-facing dashboard for monitoring, prioritising, assigning and resolving citizen complaints.
This ZIP contains **Module 5 only**. It does not regenerate Modules 1-4 or create a second app,
database or login system.

## What is included

| Area | Where |
|---|---|
| Role-gated officer API (stats, table, detail, status, classification, duplicates, map, heatmap) | `backend/app/officer/` |
| Status workflow, after-photo validation, SQL builders (framework-free, unit-tested) | `workflow.py`, `uploads.py`, `queries.py`, `priority.py` |
| The only Module 1 touch points | `integration.py` (env-configurable) |
| Module 4 adapter (duplicates, split, optional re-route) | `duplicates_gateway.py` |
| DB migration (one new table) | `backend/migrations/001_module5_classification_audit.sql` |
| React pages: Complaints, Detail, Map + heatmap, Duplicates, Login | `frontend/src/officer/` |
| Tests | `backend/tests/`, `frontend/src/officer/__tests__/` |
| Contracts and merge guide | `docs/API_CONTRACT.md`, `docs/INTEGRATION.md` |

## How it maps to the Module 5 requirements

| Requirement | Implementation |
|---|---|
| 5.2 Auth and roles | Module 1 JWT via `integration.get_current_user`; `require_officer` on every router; citizens get 403; admin-only override and reopen |
| 5.3 Stats from backend | `GET /officer/dashboard/stats`, one SQL aggregate; no hardcoded numbers |
| 5.4 Table, sort, filters, search | Server-side; HIGH first by default; filters for department, issue type, priority, status, date range; search across ID, issue, department, priority reason and report descriptions; state kept in the URL |
| 5.5 Priority display | `HIGH — 68/100` badge (red / orange / green) plus the reasons list; the score is read from Module 4 and never recalculated |
| 5.6 Detail page | Original and translated text, AI classification, confidence, severity, before photo, GPS and accuracy, report count, duplicates, priority explanation, status history, Leaflet preview |
| 5.7 Status management | Row-locked transaction updates the complaint and always inserts a `status_history` row (officer, old, new, comment, photo, time) |
| 5.8 Resolution evidence | Resolving requires an after-photo (magic-byte validated, size-limited); admin override needs a written reason and is marked in the history |
| 5.9 AI correction | `PATCH .../classification` updates the issue type and writes `classification_corrections` (old, new, officer, reason, time); the original AI label stays visible |
| 5.10 Duplicates | Review queue, confirm, reject and split, all executed by Module 4 through the gateway |
| 5.11 Map and heatmap | OpenStreetMap + Leaflet markers coloured by priority, `leaflet.heat` density layer, department / issue / priority filters, backend data only |

## Run and test

```bash
# backend (inside the Module 1 project, after copying app/officer)
pip install -r backend/requirements-module5.txt
cd backend && pytest

# frontend
cd frontend && cp .env.example .env && npm install
npm run dev      # standalone shell at http://localhost:5174/officer
npm test
```

### Verification status (please read)
Built in a sandbox with no network and without Modules 1-4, so:
* **Run and passing:** 30 backend logic tests (workflow rules, upload validation, priority parsing, SQL builders) using a minimal stand-in runner, since `pytest` could not be installed here.
* **Written but not executed:** the FastAPI role-access tests (`test_routes_access.py`) and all frontend vitest suites (dependencies unavailable offline). All Python files compile and all JS/JSX files pass an esbuild syntax check.
* **Never run against a real database.** The SQL targets PostgreSQL + PostGIS and the documented schema, but has not been executed against Module 1's actual tables. Expect small fixes at first integration; `docs/INTEGRATION.md` lists the assumptions in order of risk.

## Known limits
* The "Location" column shows coordinates; there is no reverse geocoding in the documented schema.
* Officers are not scoped to a department (the `users` table in the handoff has no department link).
* Module 5 creates no notifications; Module 6 owns that (hook point described in `docs/INTEGRATION.md`).
* Uploaded photos use local disk storage; swap `LocalStorage` for S3/MinIO if Module 1 already has object storage.
