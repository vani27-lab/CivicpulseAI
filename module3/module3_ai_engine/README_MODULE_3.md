# CivicPulse AI — Module 3: AI Intelligence Engine

Analyses a citizen's photo + description and returns category, severity (1–4), confidence,
a one-line reason, language detection and English translation. Built to the shared README
contract; independent of Modules 1, 2, 4–6.

## Test status (read this first)
- The sandbox that generated this ZIP had **no network and no fastapi/pydantic/httpx/pytest**, so the
  pytest suite in `tests/` has **not been executed**, and the live Vision API call and the HTTP route
  have **never been run**.
- What *was* run: a throwaway script exercising the parser, language detection, retry, review rule,
  saved-demo fallback and never-raise guarantee against the real module code, using stub
  `pydantic`/`httpx`. All checks passed. That is logic verification only.
- First thing to do: `pip install -r requirements-dev.txt && pytest`. Fix anything that fails
  before integrating.

## Layout
```
app/main.py                       standalone dev app (/health + /ai/classify)
app/modules/ai_engine/
  service.py     classify_complaint() + ComplaintClassifier  <- Module 4 imports this
  router.py      POST /ai/classify  (build_router(...))
  schemas.py     ClassificationResult (Pydantic) = the contract
  parser.py      strict JSON validation (dependency-free)
  vision_client.py  VisionClient protocol + Anthropic implementation
  demo_store.py / fingerprint.py   SHA-256 saved-demo fallback
  language.py    script-based language detection
  prompts.py, config.py, constants.py, exceptions.py
  persistence.py / models.py       mapping helpers / OPTIONAL SQLAlchemy mixin
data/saved_demo_results.json      demo fallback store (empty)
scripts/register_demo_result.py   add a demo entry from an image file
tests/                            pytest suite
```
Copy `app/modules/ai_engine/` into the main project (imports are relative, so the path is flexible).

## Setup
```
pip install -r requirements-dev.txt
cp .env.example .env      # set AI_VISION_API_KEY; export the vars or load via your env loader
uvicorn app.main:app --reload
pytest
```
Keys come only from environment variables. Nothing is hardcoded.

## Contract
`classify_complaint(image_bytes: bytes, description: str, language: str | None = None) -> ClassificationResult`

```json
{"issue_type":"pothole","severity":3,"confidence":0.82,"reason":"...","detected_language":"hi",
 "original_text":"...","translated_text":"...","needs_review":false,"source":"live_ai"}
```
`POST /ai/classify` — multipart: `image` (file), `description` (text, optional), `language` (optional hint).
Returns the same JSON. Errors: 413 (image over limit), 422 (no image). Everything else returns a result.

Module 4 usage:
```python
from app.modules.ai_engine import classify_complaint
ai = classify_complaint(image_bytes, description)   # never raises
```
Inject your own wiring with `set_default_classifier(ComplaintClassifier(settings, client, store))`.
Protect the route by passing Module 1's JWT dependency: `build_router(auth_dependency=get_current_user)`.

## Behaviour
| Situation | Result |
|---|---|
| Valid AI reply | `live_ai`; `needs_review = confidence < 0.70` or issue is `unclassified` |
| Malformed reply | retried once; if still invalid → `unclassified`, severity 1, confidence 0, `needs_review=true`, source `fallback` |
| API down / no key / HTTP error | look up SHA-256 of the image in saved demo store → `saved_demo` (reason prefixed `[Saved demo result]`); no match → `unclassified` as above |
| Empty, oversized or non-image bytes | `unclassified`, no API call |
| Any unexpected exception | caught → `unclassified`; complaint submission is never blocked |

## Decisions and defaults (all documented, configurable)
- **Extra `source` value `fallback`** for the Unclassified safety-net result (spec lists `live_ai`, `saved_demo`).
- **Unclassified severity = 1**, since the schema requires 1–4. Module 4 should rely on `needs_review`/`issue_type`, not that severity.
- **Language**: explicit `language` hint wins; otherwise Unicode-script detection (Hindi, Bengali, Punjabi, Gujarati, Odia, Tamil, Telugu, Kannada, Malayalam, Urdu → code; Latin → `en`; empty → `und`). If the script says `en` but the model reports another language (romanised Hindi), the model's code is used. Devanagari maps to `hi` (Marathi shares the script).
- **Translation** comes from the same vision call. English/empty text is passed through. If a non-English description comes back without a translation, `translated_text` is `""` (not the original) — treat as "translation unavailable".
- **Description is untrusted**: prompt tells the model not to follow instructions inside it.
- **Strict validation**: severity must be an integer 1–4, confidence a number 0–1, issue_type one of the 7 categories, non-empty reason (trimmed to 200 chars).
- **Default model** `claude-sonnet-4-6` via `AI_VISION_MODEL`. Other providers: implement `VisionClient.analyze()` and pass it in.
- Sync service (callable from Module 4 without an event loop); the route is a plain `def`, so FastAPI runs it in a threadpool.
- Image cap 5 MB (`AI_MAX_IMAGE_BYTES`); JPEG/PNG/WebP/GIF detected by magic bytes.

## Database
No tables created. Existing `reports` columns this module's output fills (via `persistence.report_ai_fields`):
`ai_confidence`, `ai_severity`, `translated_description`.
**Optional, not essential:** the agreed schema has nowhere to store `issue_type`, `reason`, `needs_review`, `source`
or `detected_language` per report. `models.AIResultColumnsMixin` adds them if you want them persisted (needs a
Module 1 migration). Without it Module 4 holds them in memory during processing. Note `needs_review` is needed
downstream for officer review queues, so persisting it is recommended.

## Saved demo results
```
python scripts/register_demo_result.py photo.jpg --issue-type pothole --severity 3 \
  --confidence 0.85 --reason "Large pothole on road"
```
The demo only matches byte-identical images (SHA-256). Re-saved or compressed copies will not match.

## Known limitations
- Live API call path is untested against the real service (see Test status).
- Script-based detection cannot tell Hindi from Marathi/Nepali, or Urdu from Arabic/Persian.
- No rate limiting or cost tracking.
