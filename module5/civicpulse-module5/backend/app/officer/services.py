"""Database operations for Module 5 (PostgreSQL + PostGIS, raw SQL via SQLAlchemy).

Raw SQL against the documented Module 1 tables keeps this module independent of
Module 1's ORM class names. Every state change happens in ONE transaction and
always writes a status_history row."""
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
        "priorities": ["HIGH", "MEDIUM", "LOW"],
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
        weight = max(0.1, min(1.0, score / 100.0))  # weight only; the score itself comes from Module 4
        points.append([float(p["latitude"]), float(p["longitude"]), round(weight, 3)])
    return {"points": points, "count": len(points)}


def get_complaint_detail(db, complaint_id, *, role_is_admin: bool, settings: Settings) -> dict:
    cid = str(complaint_id)
    row = db.execute(
        text(
            "SELECT c.id, c.issue_type, c.status, c.department_id, d.name AS department_name, c.report_count, "
            "c.priority_score, upper(c.priority_band) AS priority_band, c.priority_reason, c.created_at, c.updated_at, "
            "ST_Y(c.location::geometry) AS latitude, ST_X(c.location::geometry) AS longitude "
            "FROM complaints c LEFT JOIN departments d ON d.id = c.department_id WHERE c.id::text = :id"
        ),
        {"id": cid},
    ).mappings().first()
    if row is None:
        raise NotFoundError("complaint_not_found", "That complaint does not exist.")

    reports = [
        {**dict(r), "id": str(r["id"])}
        for r in db.execute(
            text(
                "SELECT id, image_url, original_description, translated_description, latitude, longitude, "
                "gps_accuracy, ai_confidence, ai_severity, created_at "
                "FROM reports WHERE complaint_id::text = :id ORDER BY created_at ASC"
            ),
            {"id": cid},
        ).mappings()
    ]
    history = [
        {
            "id": str(r["id"]),
            "old_status": _normalized(r["old_status"]),
            "new_status": _normalized(r["new_status"]),
            "officer_id": _sid(r["officer_id"]),
            "officer_name": r["officer_name"],
            "comment": r["comment"],
            "after_photo_url": r["after_photo_url"],
            "created_at": r["created_at"],
        }
        for r in db.execute(
            text(
                "SELECT h.id, h.old_status, h.new_status, h.officer_id, u.name AS officer_name, h.comment, "
                "h.after_photo_url, h.created_at FROM status_history h LEFT JOIN users u ON u.id = h.officer_id "
                "WHERE h.complaint_id::text = :id ORDER BY h.created_at ASC"
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
                "SELECT k.id, k.old_issue_type, k.new_issue_type, k.reason, k.officer_id, u.name AS officer_name, "
                "k.created_at FROM classification_corrections k LEFT JOIN users u ON u.id = k.officer_id "
                "WHERE k.complaint_id::text = :id ORDER BY k.created_at ASC"
            ),
            {"id": cid},
        ).mappings()
    ]

    primary = reports[0] if reports else {}
    current_status = normalize_status(row["status"])
    allowed = allowed_next(current_status, role_is_admin, settings.enable_rejected) if current_status else []
    after_photo = next((h["after_photo_url"] for h in reversed(history) if h["after_photo_url"]), None)

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
        },
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
        "before_photo_url": primary.get("image_url"),
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

    # Lock the row so two officers cannot move the same complaint at once.
    row = db.execute(
        text("SELECT id, status FROM complaints WHERE id::text = :id FOR UPDATE"), {"id": cid}
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

        history_id = uuid.uuid4()
        db_status = to_db_value(new_status, settings.status_style)
        updated = db.execute(
            text("UPDATE complaints SET status = :s, updated_at = now() WHERE id::text = :id RETURNING updated_at"),
            {"s": db_status, "id": cid},
        ).scalar_one()
        db.execute(
            text(
                "INSERT INTO status_history (id, complaint_id, officer_id, old_status, new_status, comment, "
                "after_photo_url, created_at) VALUES (:hid, :cid, :oid, :old, :new, :comment, :photo, now())"
            ),
            {
                "hid": history_id,
                "cid": row["id"],
                "oid": officer_id,
                "old": row["status"],  # stored exactly as it was
                "new": db_status,
                "comment": history_comment,
                "photo": saved.url if saved else None,
            },
        )
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
        "history_id": str(history_id),
        "after_photo_url": saved.url if saved else None,
        "override_used": override_used,
        "updated_at": updated,
    }


def correct_classification(db, *, complaint_id, officer_id, new_issue_type: str, reason: str | None) -> dict:
    new_value = " ".join(new_issue_type.split())
    if len(new_value) < 2:
        raise ValidationFailed("bad_issue_type", "Enter the corrected issue type.")
    cid = str(complaint_id)

    row = db.execute(
        text("SELECT id, issue_type FROM complaints WHERE id::text = :id FOR UPDATE"), {"id": cid}
    ).mappings().first()
    if row is None:
        db.rollback()
        raise NotFoundError("complaint_not_found", "That complaint does not exist.")
    if (row["issue_type"] or "").strip().lower() == new_value.lower():
        db.rollback()
        raise ValidationFailed("unchanged", "The issue type is already set to that value.")

    correction_id = uuid.uuid4()
    try:
        db.execute(
            text("UPDATE complaints SET issue_type = :t, updated_at = now() WHERE id::text = :id"),
            {"t": new_value, "id": cid},
        )
        db.execute(
            text(
                "INSERT INTO classification_corrections (id, complaint_id, officer_id, old_issue_type, "
                "new_issue_type, reason, created_at) VALUES (:id, :cid, :oid, :old, :new, :reason, now())"
            ),
            {
                "id": correction_id,
                "cid": row["id"],
                "oid": officer_id,
                "old": row["issue_type"],
                "new": new_value,
                "reason": (reason or "").strip() or None,
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
        "correction_id": str(correction_id),
    }
