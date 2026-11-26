# CivicPulse AI — Module 6: Citizen Tracking & Integration

## Contents
- `backend/app/modules/citizen_tracking/` — FastAPI router (not a new app), translation service, shaping helpers
- `backend/migrations/006_citizen_tracking.sql` — new tables `notifications`, `comment_translations` + trigger
- `frontend/src/modules/citizen/` — pages, components, i18n (en, hi), TTS hook, API client
- Tests: `backend/tests/test_module6.py` (pytest), `frontend/src/modules/citizen/__tests__/timeline.test.js` (vitest)

## Install
1. Run `006_citizen_tracking.sql` against the single PostgreSQL DB.
2. `pip install -r backend/requirements-module6.txt`
3. In Module 1's `main.py`, **before** any generic `/complaints/{id}` route:
   `from app.modules.citizen_tracking.router import router as citizen_router; app.include_router(citizen_router)`
4. Copy `frontend/src/modules/citizen` into the app; add `citizenRoutes` to the router; merge `package.additions.json`; copy `.env.example`.
5. Tailwind `content` must include `./src/modules/**/*.{js,jsx}`.

## Assumptions (change here if Module 1 differs)
- UUID ids; status values `submitted|assigned|in_progress|resolved|rejected` (case/space-insensitive).
- Module 1 exposes `app.database:get_db` (SQLAlchemy Session) and `app.auth:get_current_user` (object or dict with `id`). Override with env `M1_GET_DB`, `M1_GET_CURRENT_USER` (`module.path:name`).
- JWT stored in `localStorage["token"]` (`VITE_TOKEN_KEY`). Login route `/login` (`VITE_LOGIN_PATH`).
- Citizen ownership = a row in `reports` with `user_id` = caller. Non-owned complaints return **404** (not 403) so existence isn't revealed.
- Image URLs in `reports.image_url` / `status_history.after_photo_url` are served by Modules 2/5 (relative paths are prefixed with `VITE_API_URL`).
- Module 2 inserts an initial `submitted` row in `status_history`; if not, the "Submitted" notification and timeline step won't appear.
- Citizens who reported a merged duplicate see the merged complaint's status (via their own `reports` row).

## Privacy
Citizen endpoints never return `officer_id`, AI scores, `priority_score`, `priority_reason`, other citizens' reports or `report_count`. After-photos are exposed only on `resolved` entries.

## Notifications
A DB trigger on `status_history` inserts in-app notifications for every citizen who reported that complaint, so Module 5 needs no changes. Email/SMS: add a worker that reads `notifications`.

## Translation
Default off (UI is still fully bilingual; officer comments show in English). Enable: `TRANSLATION_PROVIDER=libretranslate`, `LIBRETRANSLATE_URL=...`. Results are cached in `comment_translations`; any failure falls back to the original comment. Translation runs at read time, so it can never block an officer update.
Add a language: `i18n/xx.js` + one line in `LANGUAGES`.

## Integration checklist (spec §7)
| # | Check | Covered by |
|---|---|---|
| 1, 10 | Same auth/DB | `deps.py` adapter, SQL on shared tables |
| 5, 6 | status_history → tracking | `/history`, `buildTimeline` (no fake progress) |
| 7 | Descriptions preserved | detail page shows original + English |
| 8 | Before/after | `BeforeAfter` |
| 9 | RBAC | JWT + ownership on every route |
| 2, 3, 4 | Module 2→3→4 pipeline | **Manual E2E needed** (not verifiable from this module) |

## Not included
Playwright/E2E suite, email/SMS, extra languages, notification preferences, component-level React tests (only timeline logic is tested).
