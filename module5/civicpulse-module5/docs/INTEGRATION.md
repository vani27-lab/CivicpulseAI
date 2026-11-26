# Integrating Module 5 into the main repository

Module 5 was built without access to Modules 1-4, from the handoff's documented schema. Every
guess is isolated so a mismatch is a one-line change, not a rewrite.

## 1. Backend (5 steps)
1. Copy `backend/app/officer/` into the FastAPI project as `app/officer/`.
2. Run `backend/migrations/001_module5_classification_audit.sql` (adds ONE table, `classification_corrections`, plus optional indexes).
3. `pip install -r backend/requirements-module5.txt` (the important one is `python-multipart`) and merge `backend/.env.example` into the backend `.env`.
4. In `main.py`: `from app.officer import include_module5_routers` then `include_module5_routers(app)`.
5. Serve the upload directory. In Docker Compose give the backend a volume and expose it, for example:
   ```yaml
   services:
     backend:
       volumes:
         - uploads:/data/uploads
   volumes:
     uploads:
   ```
   and in FastAPI: `app.mount("/media", StaticFiles(directory="/data/uploads"), name="media")` (skip if Module 1 already serves `/media`).

## 2. Assumptions to verify (in order of likelihood to differ)
| Assumption | Where to change |
|---|---|
| DB session dependency is `app.db.session:get_db`; auth dependency is `app.core.security:get_current_user` returning an object/dict with `id`, `name`, `role` | env `M5_GET_DB`, `M5_GET_CURRENT_USER` |
| Roles stored as `officer`, `admin`, `citizen` | env `M5_OFFICER_ROLES`, `M5_ADMIN_ROLE` |
| `complaints.status` stored as `snake_case` (`in_progress`); `title` also supported | env `M5_STATUS_STYLE` |
| `complaints.location` is a PostGIS geometry/geography point (read with `ST_X/ST_Y`) | `queries.py` |
| `reports.latitude/longitude` are numeric columns | `services.get_complaint_detail` |
| `priority_reason` is a JSON list, `{"reasons": [...]}`, or text split by newline/semicolon | `priority.parse_reasons` |
| UUID primary keys | `ComplaintId` in `schemas.py` |
| Module 4 exposes the functions listed in `duplicates_gateway.py` | `duplicates_gateway.py` (4 thin wrappers) |
| Module 4 already serves `/stats/heatmap` or duplicate routes | set `M5_MOUNT_HEATMAP=false` / `M5_MOUNT_DUPLICATE_ROUTES=false` and update `frontend/src/officer/config.js` paths |
| Module 1 stores the JWT in `localStorage` under one key; `/auth/login` returns `access_token`; `/auth/me` returns `{id, name, email, role}` | frontend env `VITE_AUTH_*` |

## 3. Frontend
1. Copy `frontend/src/officer/` into the app's `src/`. Merge `package.json` dependencies (`react-router-dom`, `leaflet`, `react-leaflet@4`, `leaflet.heat`) and `tailwind.config.js` colour tokens.
2. Add `<Route path="/officer/*" element={<OfficerRoutes />} />` (import from `./officer`).
3. If Module 1's frontend already has an auth context, replace `officer/auth/session.jsx` with a wrapper around it; nothing else reads the token.
4. Merge `.env.example` values.

## 4. Handoff notes for Module 6
* Citizen tracking should read the same `status_history` rows; after-photos are in `status_history.after_photo_url` on the resolving row.
* `officer/lib/labels.js` and `tailwind.config.js` hold the shared status/priority tokens; reuse them for visual consistency.
* The officer comment typed in the status form is stored verbatim in `status_history.comment`; Module 6 can translate it for the citizen.
* Module 5 does not create notifications. Hook point: after `services.update_status` commits, Module 6 can enqueue an in-app notification keyed on the returned `history_id`.
