# Module 5 API contract

All routes require a valid Module 1 JWT **and** an officer/admin role (`M5_OFFICER_ROLES`).
Citizens get `403`, anonymous callers get `401` (from Module 1's `get_current_user`).
Errors use `{"detail": {"code": "...", "message": "..."}}`. Statuses are always returned
normalised (`submitted | assigned | in_progress | resolved | rejected`).

| Method | Path | Purpose |
|---|---|---|
| GET | `/officer/dashboard/stats` | `{total, pending, in_progress, resolved, high_priority}` computed in SQL |
| GET | `/officer/filters` | Departments, issue types, statuses, priorities for filter dropdowns |
| GET | `/officer/complaints` | Paged table. Query: `q, department_id, issue_type, priority, status, date_from, date_to, sort_by, sort_dir, page, page_size` |
| GET | `/officer/complaints/map` | Marker data (`id, issue_type, status, priority_band, priority_score, report_count, latitude, longitude`); same filters plus `active_only` |
| GET | `/officer/complaints/{id}` | Full detail incl. reports, history, corrections, duplicate candidates, `allowed_next_statuses`, `can_override` |
| PATCH | `/complaints/{id}/status` | `multipart/form-data`: `new_status`, `comment?`, `after_photo?`, `admin_override?`, `override_reason?` |
| PATCH | `/complaints/{id}/classification` | JSON `{issue_type, reason?}`; writes `classification_corrections` |
| GET | `/officer/complaints/duplicates` | Adapter to Module 4 (`status=pending, page, page_size`) |
| POST | `/officer/duplicates/{candidate_id}/confirm` | Adapter to Module 4 |
| POST | `/officer/duplicates/{candidate_id}/reject` | Adapter to Module 4 |
| POST | `/complaints/{id}/split` | JSON `{report_ids[], reason}`; adapter to Module 4 |
| GET | `/stats/heatmap` | `{points: [[lat, lng, weight 0..1]], count}`; open complaints unless `status` is given |

## Sorting
`sort_by`: `priority` (default), `priority_score`, `created_at`, `updated_at`, `report_count`, `status`, `issue_type`, `department`.
`sort_by=priority&sort_dir=desc` returns HIGH first, then highest score, then oldest. Anything else returns `422 bad_sort`.

## Status workflow (server-enforced)
```
submitted -> assigned | rejected
assigned  -> in_progress | rejected
in_progress -> resolved | assigned | rejected
resolved / rejected -> (admin only) in_progress / submitted
```
* `resolved` requires a valid JPEG/PNG/WebP `after_photo` (magic-byte checked, 8 MB default).
* `rejected` requires a comment.
* `admin_override=true` (admin only, with a written reason) bypasses transition and photo rules; the history comment is prefixed `[Admin override: ...]`.
* Each change updates `complaints.status` and inserts one `status_history` row (officer, old status, new status, comment, after-photo URL, timestamp) in **one transaction** under a row lock. A failed write deletes the just-saved photo.

## Error codes
`invalid_transition, same_status, after_photo_required, comment_required, override_forbidden, override_reason_required, photo_only_for_resolution, unsupported_type (415), file_too_large (413), empty_upload, bad_status, bad_priority, bad_sort, unchanged, complaint_not_found (404), duplicate_service_unavailable (501)`.
