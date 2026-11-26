# CivicPulse AI — Module 4: Complaint Intelligence Engine

Takes a new citizen report (image + GPS), calls Module 3, detects duplicates (PostGIS distance **and**
CLIP image similarity), merges or creates a complaint, calculates explainable priority, routes to a
department and saves. Built to the shared README contract; independent of Modules 1, 2, 5, 6.

## Test status (read this first)
The generating sandbox had no network, no PostgreSQL/PostGIS and no fastapi/pydantic/sqlalchemy/pytest.
- **Executed here (passing):** 64 unit tests covering priority formula and bands, explanations, GPS
  validation, location factor, routing, duplicate decisions, and the full process/merge/split flow
  against the in-memory repository. They ran through a minimal pytest shim and a pydantic stub, not the
  real libraries.
- **NOT executed, never run:** `repository_sqlalchemy.py` (all PostGIS SQL incl. `ST_DWithin`),
  the FastAPI routes (`tests/test_router.py` was written but skips without fastapi), `ClipEmbedder`
  (no model download possible), and `app/main.py`.
- First steps: `pip install -r requirements-dev.txt && pytest`, then run the SQL repository against a
  Module 1 database. Expect to fix small SQL/driver issues there.

## Layout
```
app/main.py                           standalone dev app (needs DATABASE_URL)
app/modules/complaint_engine/
  engine.py        ComplaintProcessor: process / priority / duplicates / split   <- main entry point
  priority.py      exact formula, bands, explanations           (pure Python)
  duplicates.py    cosine + merge/possible/new decision          (pure Python)
  gps.py, places.py, routing.py                                  (pure Python)
  repository.py    interface;  repository_sqlalchemy.py (PostGIS);  repository_memory.py (tests/dev)
  embedder.py      CLIP (lazy import) / Null
  schemas.py, router.py, config.py, domain.py, constants.py, exceptions.py
data/places.json                      points of interest (EMPTY by default, see Known limitations)
tests/                                pytest suite + helpers
```
Copy `app/modules/complaint_engine/` into the main project (imports are relative).

## Setup
```
pip install -r requirements-dev.txt
pip install -r requirements-clip.txt      # only for real CLIP embeddings (large: torch)
cp .env.example .env
pytest
DATABASE_URL=... uvicorn app.main:app     # dev only
```
Departments must already exist in `departments` with these names (case-insensitive):
**Roads, Sanitation, Electrical, Drainage, Manual review**. Module 4 never creates departments; a missing
one yields `department_id = null` plus a `department_not_found:<name>` warning.

## Endpoints
| Endpoint | Purpose |
|---|---|
| `POST /complaints/process` | multipart: `image`, `latitude`, `longitude`, optional `description`, `language`, `gps_accuracy`, `image_url`, `report_id` → `ProcessResult` |
| `GET /complaints/{id}/priority` | live priority + reasons + component breakdown (+ stored values) |
| `GET /complaints/{id}/duplicates` | the reports merged into this complaint + possible duplicates |
| `POST /complaints/{id}/split` | JSON `{report_ids:[...], comment}`; officers only |

Errors: 422 invalid GPS, 413 oversized image, 404 unknown complaint, 409 disallowed split, 403 non-officer,
**503 on split if no officer auth dependency was supplied (fails closed)**.

Wiring into the main app:
```python
build_router(processor_provider=get_processor,           # returns ComplaintProcessor for the request's DB session
             user_dependency=get_current_user,           # .id becomes reports.user_id
             officer_dependency=get_current_user)        # needs .id and .role in CP_OFFICER_ROLES
```
`user_id` is deliberately *not* accepted from the form (it could be spoofed).

## Contract
Consumes Module 3's `classify_complaint(image_bytes, description, language=None)` result (object or dict
with `issue_type, severity, confidence, reason, detected_language, original_text, translated_text,
needs_review, source`). Inputs are re-validated; bad values degrade to severity 1 / unclassified.
Module 3 is imported lazily via `default_classifier()` (path `app.modules.ai_engine`; edit if yours differs),
or inject any callable: `ComplaintProcessor(repo, classifier=..., embedder=..., places=..., settings=...)`.

Produces (`ProcessResult`): `complaint_id, duplicate_status, report_count, priority_score, priority_band,
priority_reason, department_id`, plus these additions: `report_id, issue_type, severity, needs_review,
ai_source, similarity, possible_duplicate_ids, department_name, warnings`.
`duplicate_status` ∈ `new | merged | possible_duplicate`.

Module 2 handoff: if Module 2 already inserted the `reports` row, pass its id as `report_id` and Module 4
attaches and enriches it (complaint_id, AI fields, embedding). Otherwise Module 4 inserts the report.

## Processing flow (as implemented)
1. Module 3 classification (a raised exception becomes `unclassified`; submission is never blocked)
2. GPS validation (finite, in range, not 0,0, inside the service-area box → else `InvalidGPSError`/422)
3. Candidate search: same `issue_type`, `ST_DWithin` 50 m, complaint `created_at` within 30 days, eligible status
4. CLIP comparison: max cosine similarity between the new image and every report already on the candidate
5. Decision — **distance alone never confirms**:
   - similarity ≥ merge threshold (0.92) → **merged**
   - similarity ≥ possible threshold (0.85), or no embedding available to compare → **possible_duplicate** (new complaint, flagged)
   - otherwise → **new**
   - GPS accuracy worse than 50 m downgrades an automatic merge to *possible*
   - `unclassified` reports are never merged (`CP_MERGE_UNCLASSIFIED` to change)
6. Merge keeps every report row, `report_count` is recounted from `reports`, priority recalculated
7. Routing via the departments table; save; single commit (rollback on any error)

## Priority
Exact formula from the spec (natural log). `days_pending` is **whole days** since the complaint's
`created_at` (floored) so the stated reason matches the maths. `severity` is the **highest** `ai_severity`
across the complaint's reports (the schema has no complaint-level severity). Score is stored rounded to
2 decimals and the band is decided from that stored value. HIGH: score ≥ 60 or severity 4; MEDIUM ≥ 40; else LOW.
`priority_reason` is stored like:
```
HIGH — 72.6/100
Reasons:
- Serious road damage.
- 5 citizen reports.
- Pending for 9 days.
- School nearby.
```
Every line is emitted only if that factor is actually present in the calculation.
Stored scores go stale as days pass: `GET /priority` always recalculates live, and
`ComplaintProcessor.refresh_open_priorities()` is provided for a scheduler (cron/Celery) to persist updates. Nothing schedules it for you.

## Split
Moves the chosen reports to a brand-new complaint (same category and department; earliest moved report sets
its location and age), recounts and re-prioritises both, and writes one `status_history` row on each
complaint with the officer id. It refuses to move *all* reports. The new complaint's category is copied
from the original because `reports` carries no `issue_type`; an officer can reclassify afterwards.

## Decisions and defaults (all configurable, see `.env.example`)
- Statuses eligible for merging: `submitted, acknowledged, in_progress`; new complaints start as `submitted`.
  **Match these to Module 1/5's real status values.**
- "Within 30 days" is measured on the candidate complaint's `created_at`.
- Category `other` is routed to "Manual review" (not in the agreed routing table).
- No new tables. Possible duplicates are recomputed on demand rather than stored. The location factor reads
  `data/places.json` because the agreed schema has no places table.
- Embeddings: CLIP `clip-ViT-B-32` via sentence-transformers, L2-normalised, stored in `reports.image_embedding`.
  The column type is unknown, so `SqlAlchemyComplaintRepository` takes `embedding_to_db/from_db` adapters
  (default fits `float8[]`; pgvector needs adapters).
- Sync SQLAlchemy 2.x Session assumed. An async stack needs an async repository implementing the same interface.
- `ProcessResult.needs_review` is true when Module 3 flagged it or the result is a possible duplicate. There is
  no column for it in the agreed schema, so it is only returned, not persisted.

## Known limitations
- **Similarity thresholds are uncalibrated guesses.** Different potholes on the same road can look alike to CLIP,
  and the same pothole from two angles may not. Test on real photos before trusting auto-merge.
- **Chain drift:** a new image is compared with *every* report on a complaint and the best match counts, so a
  gradual sequence of slightly different photos can merge transitively. Officers can undo it with split.
- **Location factor is zero everywhere until you load `places.json`** (a warning is logged). It only supports
  points, so a main road needs sampled points or a per-entry `radius_m`. A PostGIS-backed `PlaceProvider` is the natural upgrade.
- No locking: two near-simultaneous reports of the same issue can each create a complaint. They would show as
  possible duplicates of each other on the next lookup, not merge automatically.
- Priority bands are decided on the stored (2-decimal) score; `/priority` may differ from the stored value
  simply because time has passed.
