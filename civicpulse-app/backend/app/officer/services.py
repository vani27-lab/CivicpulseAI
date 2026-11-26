"""Database operations for Module 5 (compatible with PostgreSQL and SQLite).

Every state change happens in ONE transaction and always writes a status_history row.
"""
from datetime import datetime
import logging
import uuid

from sqlalchemy import text

from . import duplicates_gateway
from .config import Settings
from .errors import NotFoundError, ValidationFailed
from .priority import parse_reasons
from .queries import (
    FILTER_OPTIONS_SQL,
    STATS_SQL,
    ComplaintFilters,
    build_list_sql,
    build_map_sql,
)
from .uploads import LocalStorage, ValidatedImage
from .workflow import STATUS_LABELS, Status, allowed_next, normalize_status, to_db_value, validate_transition

log = logging.getLogger(__name__)


def _sid(value):
    return None if value is None else str(value)


def get_stats(db) -> dict:
    row = db.execute(text(STATS_SQL)).mappings().one()
    return {k: int(row[k] or 0) for k in ("total", "pending", "in_progress", "resolved", "high_priority")}


def get_filter_options(db) -> dict:
    departments = [{"id": str(r["id"]), "name": r["name"]} for r in db.execute(text(FILTER_OPTIONS_SQL["departments"])).mappings()]
    issue_types = [r["issue_type"] for r in db.execute(text(FILTER_OPTIONS_SQL["issue_types"])).mappings()]
    return {
        "departments": departments,
        "issue_types": issue_types,
        "statuses": [{"value": s.value, "label": STATUS_LABELS[s]} for s in Status],
        "priorities": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    }


def list_complaints(db, filters: ComplaintFilters, sort_by: str, sort_dir: str, page: int, page_size: int) -> dict:
    list_sql, count_sql, params = build_list_sql(filters, sort_by, sort_dir, page, page_size)
    total = db.execute(text(count_sql), {k: v for k, v in params.items() if k not in ("limit", "offset")}).scalar_one()
    rows = db.execute(text(list_sql), params).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["id"] = str(item["id"])
        item["department_id"] = _sid(item["department_id"])
        item["report_count"] = int(item["report_count"] or 0)
        item["is_emergency"] = bool(item.get("is_emergency"))
        items.append(item)
    return {"items": items, "total": int(total), "page": max(1, page), "page_size": max(1, min(page_size, 100))}


def get_map_points(db, filters: ComplaintFilters) -> list[dict]:
    sql, params = build_map_sql(filters)
    return [
        {**dict(r), "id": str(r["id"]), "report_count": int(r["report_count"] or 0)}
        for r in db.execute(text(sql), params).mappings()
    ]


def get_heatmap(db, filters: ComplaintFilters) -> dict:
    points = []
    for p in get_map_points(db, filters):
        score = float(p["priority_score"] or 0)
        weight = max(0.1, min(1.0, score / 100.0))
        points.append([float(p["latitude"]), float(p["longitude"]), round(weight, 3)])
    return {"points": points, "count": len(points)}


def _normalize_media_url(path: str | None) -> str | None:
    if not path:
        return None
    p = str(path).strip()
    if p.startswith("http://") or p.startswith("https://") or p.startswith("data:") or p.startswith("blob:"):
        return p
    if p.startswith("/uploads/") or p.startswith("/media/"):
        return p
    if p.startswith("uploads/"):
        return f"/{p}"
    if p.startswith("media/"):
        return f"/{p}"
    if p.startswith("/"):
        return f"/uploads{p}"
    return f"/uploads/{p}"


def get_complaint_detail(db, complaint_id, *, role_is_admin: bool, settings: Settings) -> dict:
    cid = str(complaint_id)
    row = db.execute(
        text(
            "SELECT c.id, COALESCE(c.issue_type, c.category) AS issue_type, c.status, c.department_id, d.name AS department_name, c.report_count, "
            "c.priority_score, upper(COALESCE(c.priority_band, c.priority_level)) AS priority_band, COALESCE(c.priority_reason, c.priority_explanation) AS priority_reason, "
            "c.created_at, c.updated_at, c.latitude AS latitude, c.longitude AS longitude, "
            "c.before_photo_path, c.after_photo_path, "
            "c.nearest_facility_name, c.nearest_facility_type, c.nearest_facility_distance_m, "
            "c.nearby_facilities_json, c.citizen_urgency_reason, c.is_emergency "
            "FROM complaints c LEFT JOIN departments d ON d.id = c.department_id WHERE CAST(c.id AS TEXT) = :id"
        ),
        {"id": cid},
    ).mappings().first()
    if row is None:
        raise NotFoundError("complaint_not_found", "That complaint does not exist.")

    reports = [
        {**dict(r), "id": str(r["id"]), "image_url": _normalize_media_url(r["image_url"])}
        for r in db.execute(
            text(
                "SELECT id, COALESCE(image_url, image_path) AS image_url, description_original AS original_description, "
                "description_english AS translated_description, latitude, longitude, "
                "location_accuracy_m AS gps_accuracy, NULL AS ai_confidence, NULL AS ai_severity, created_at "
                "FROM reports WHERE CAST(complaint_id AS TEXT) = :id ORDER BY created_at ASC"
            ),
            {"id": cid},
        ).mappings()
    ]
    history = [
        {
            "id": str(r["id"]),
            "old_status": _normalized(r["old_status"] or r["status"]),
            "new_status": _normalized(r["new_status"] or r["status"]),
            "officer_id": _sid(r["officer_id"] or r["changed_by_id"]),
            "officer_name": r["officer_name"],
            "comment": r["comment"] or r["note"],
            "after_photo_url": _normalize_media_url(r["after_photo_url"] or (r["photo_path"] if (_normalized(r["new_status"] or r["status"]) == "resolved") else None)),
            "created_at": r["created_at"],
        }
        for r in db.execute(
            text(
                "SELECT h.id, h.old_status, h.new_status, h.status, h.officer_id, h.changed_by_id, "
                "COALESCE(u.name, u.full_name) AS officer_name, h.comment, h.note, "
                "h.after_photo_url, h.photo_path, h.created_at FROM status_history h "
                "LEFT JOIN users u ON u.id = COALESCE(h.officer_id, h.changed_by_id) "
                "WHERE CAST(h.complaint_id AS TEXT) = :id ORDER BY h.created_at ASC"
            ),
            {"id": cid},
        ).mappings()
    ]
    corrections = [
        {
            "id": str(r["id"]),
            "old_issue_type": r["old_issue_type"],
            "new_issue_type": r["new_issue_type"],
            "reason": r["reason"],
            "officer_id": _sid(r["officer_id"]),
            "officer_name": r["officer_name"],
            "created_at": r["created_at"],
        }
        for r in db.execute(
            text(
                "SELECT k.id, k.old_issue_type, k.new_issue_type, k.reason, k.officer_id, "
                "COALESCE(u.name, u.full_name) AS officer_name, k.created_at "
                "FROM classification_corrections k LEFT JOIN users u ON u.id = k.officer_id "
                "WHERE CAST(k.complaint_id AS TEXT) = :id ORDER BY k.created_at ASC"
            ),
            {"id": cid},
        ).mappings()
    ]

    primary = reports[0] if reports else {}
    current_status = normalize_status(row["status"])
    allowed = allowed_next(current_status, role_is_admin, settings.enable_rejected) if current_status else []
    after_photo = _normalize_media_url(row.get("after_photo_path")) or next((h["after_photo_url"] for h in reversed(history) if h["after_photo_url"]), None)

    import json
    nearest_name = row.get("nearest_facility_name")
    nearest_type = row.get("nearest_facility_type")
    nearest_dist = row.get("nearest_facility_distance_m")
    nearby_facs = json.loads(row.get("nearby_facilities_json") or "[]") if row.get("nearby_facilities_json") else []
    is_emergency = bool(row.get("is_emergency"))
    citizen_urgency = row.get("citizen_urgency_reason")

    if not nearest_name and row.get("latitude") and row.get("longitude"):
        try:
            from app.services.geo_facility_service import analyze_geospatial_impact
            geo_res = analyze_geospatial_impact(
                lat=float(row["latitude"]),
                lon=float(row["longitude"]),
                issue_type=row["issue_type"] or "other",
                severity=1,
                db=db,
            )
            if geo_res.nearest_facility:
                nearest_name = geo_res.nearest_facility.name
                nearest_type = geo_res.nearest_facility.facility_type
                nearest_dist = geo_res.nearest_facility.distance_m
                nearby_facs = [
                    {"name": f.name, "type": f.facility_type, "distance_m": f.distance_m, "lat": f.latitude, "lon": f.longitude}
                    for f in geo_res.nearby_facilities
                ]
                is_emergency = geo_res.is_emergency
                citizen_urgency = geo_res.citizen_urgency_reason
        except Exception:
            pass

    return {
        "id": str(row["id"]),
        "issue_type": row["issue_type"],
        "status": current_status.value if current_status else None,
        "department_id": _sid(row["department_id"]),
        "department_name": row["department_name"],
        "report_count": int(row["report_count"] or len(reports)),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "gps_accuracy": primary.get("gps_accuracy"),
        "priority": {
            "score": row["priority_score"],
            "band": row["priority_band"],
            "reasons": parse_reasons(row["priority_reason"]),
            "nearest_facility_name": nearest_name,
            "nearest_facility_type": nearest_type,
            "nearest_facility_distance_m": nearest_dist,
            "is_emergency": is_emergency,
            "citizen_urgency_reason": citizen_urgency,
            "nearby_facilities": nearby_facs,
        },
        "nearby_facilities": nearby_facs,
        "nearest_facility": {
            "name": nearest_name,
            "type": nearest_type,
            "distance_m": nearest_dist,
        } if nearest_name else None,
        "is_emergency": is_emergency,
        "citizen_urgency_reason": citizen_urgency,
        "ai_classification": {
            "original_issue_type": corrections[0]["old_issue_type"] if corrections else row["issue_type"],
            "current_issue_type": row["issue_type"],
            "corrected": bool(corrections),
            "confidence": primary.get("ai_confidence"),
            "severity": primary.get("ai_severity"),
        },
        "reports": reports,
        "history": history,
        "corrections": corrections,
        "duplicate_candidates": duplicates_gateway.candidates_for(db, cid),
        "allowed_next_statuses": [s.value for s in allowed],
        "can_override": role_is_admin,
        "before_photo_url": _normalize_media_url(row.get("before_photo_path") or primary.get("image_url")),
        "after_photo_url": after_photo,
    }


def _normalized(raw):
    status = normalize_status(raw)
    return status.value if status else (str(raw) if raw is not None else None)


def update_status(
    db,
    *,
    complaint_id,
    officer_id,
    role_is_admin: bool,
    new_status_raw: str,
    comment: str | None,
    photo: ValidatedImage | None,
    admin_override: bool,
    override_reason: str | None,
    storage: LocalStorage,
    settings: Settings,
) -> dict:
    new_status = normalize_status(new_status_raw)
    if new_status is None:
        raise ValidationFailed("bad_status", "Unknown status.")
    if photo is not None and new_status is not Status.RESOLVED:
        raise ValidationFailed("photo_only_for_resolution", "An after-photo can only be attached when resolving.")

    comment = (comment or "").strip() or None
    cid = str(complaint_id)

    row = db.execute(
        text("SELECT id, status FROM complaints WHERE CAST(id AS TEXT) = :id"), {"id": cid}
    ).mappings().first()
    if row is None:
        db.rollback()
        raise NotFoundError("complaint_not_found", "That complaint does not exist.")

    saved = None
    try:
        override_used = validate_transition(
            normalize_status(row["status"]),
            new_status,
            role_is_admin=role_is_admin,
            comment=comment,
            has_after_photo=photo is not None,
            admin_override=admin_override,
            override_reason=override_reason,
            rejected_enabled=settings.enable_rejected,
        )
        if photo is not None:
            saved = storage.save(cid, photo)

        history_comment = comment
        if override_used:
            note = f"[Admin override: {override_reason.strip()}]"
            history_comment = f"{note} {comment}" if comment else note

        history_id = str(uuid.uuid4())
        db_status = to_db_value(new_status, settings.status_style)
        now_ts = datetime.utcnow()

        db.execute(
            text(
                "UPDATE complaints SET status = :s, updated_at = :ts, "
                "after_photo_path = COALESCE(:photo, after_photo_path), "
                "resolved_at = CASE WHEN :is_resolved THEN :ts ELSE resolved_at END "
                "WHERE CAST(id AS TEXT) = :id"
            ),
            {
                "s": db_status,
                "ts": now_ts,
                "photo": saved.url if saved else None,
                "is_resolved": (new_status == Status.RESOLVED),
                "id": cid,
            },
        )
        db.execute(
            text(
                "INSERT INTO status_history (complaint_id, officer_id, changed_by_id, old_status, new_status, status, "
                "comment, note, after_photo_url, photo_path, created_at) "
                "VALUES (:cid, :oid, :oid, :old, :new, :new, :comment, :comment, :photo, :photo, :ts)"
            ),
            {
                "cid": row["id"],
                "oid": officer_id,
                "old": row["status"],
                "new": db_status,
                "comment": history_comment,
                "photo": saved.url if saved else None,
                "ts": now_ts,
            },
        )

        # Trigger notification for citizens who submitted reports for this complaint (Module 6)
        try:
            reports = db.execute(
                text("SELECT DISTINCT citizen_id FROM reports WHERE CAST(complaint_id AS TEXT) = :cid"),
                {"cid": cid}
            ).fetchall()
            for r in reports:
                if r[0]:
                    db.execute(
                        text(
                            "INSERT INTO notifications (id, user_id, complaint_id, kind, status, is_read, created_at) "
                            "VALUES (:nid, :uid, :cid, 'status_change', :st, 0, :ts)"
                        ),
                        {
                            "nid": str(uuid.uuid4()),
                            "uid": r[0],
                            "cid": row["id"],
                            "st": db_status,
                            "ts": now_ts,
                        }
                    )
        except Exception as e:
            log.warning("Notification insert error: %s", e)

        db.commit()
    except Exception:
        db.rollback()
        if saved:
            storage.delete(saved.relative_path)
        raise

    return {
        "complaint_id": cid,
        "old_status": _normalized(row["status"]),
        "new_status": new_status.value,
        "history_id": history_id,
        "after_photo_url": saved.url if saved else None,
        "override_used": override_used,
        "updated_at": now_ts,
    }


def correct_classification(db, *, complaint_id, officer_id, new_issue_type: str, reason: str | None) -> dict:
    new_value = " ".join(new_issue_type.split())
    if len(new_value) < 2:
        raise ValidationFailed("bad_issue_type", "Enter the corrected issue type.")
    cid = str(complaint_id)

    row = db.execute(
        text("SELECT id, category AS issue_type FROM complaints WHERE CAST(id AS TEXT) = :id"), {"id": cid}
    ).mappings().first()
    if row is None:
        db.rollback()
        raise NotFoundError("complaint_not_found", "That complaint does not exist.")
    if (row["issue_type"] or "").strip().lower() == new_value.lower():
        db.rollback()
        raise ValidationFailed("unchanged", "The issue type is already set to that value.")

    correction_id = str(uuid.uuid4())
    now_ts = datetime.utcnow()
    try:
        db.execute(
            text("UPDATE complaints SET category = :t, issue_type = :t, updated_at = :ts WHERE CAST(id AS TEXT) = :id"),
            {"t": new_value, "ts": now_ts, "id": cid},
        )
        db.execute(
            text(
                "INSERT INTO classification_corrections (id, complaint_id, officer_id, old_issue_type, "
                "new_issue_type, reason, created_at) VALUES (:id, :cid, :oid, :old, :new, :reason, :ts)"
            ),
            {
                "id": correction_id,
                "cid": row["id"],
                "oid": officer_id,
                "old": row["issue_type"],
                "new": new_value,
                "reason": (reason or "").strip() or None,
                "ts": now_ts,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    duplicates_gateway.maybe_reroute(db, cid)
    return {
        "complaint_id": cid,
        "old_issue_type": row["issue_type"],
        "new_issue_type": new_value,
        "correction_id": correction_id,
    }
