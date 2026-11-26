"""Module 4 duplicate service implementation for officer dashboard integration.

Supports:
- Proximity and category based duplicate candidate discovery
- Candidate list & per-complaint duplicate lookup
- Officer confirm/reject merge actions
- Report split into new complaint with status history logging
"""
import math
from datetime import datetime
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Complaint, Report, StatusHistory


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # meters
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def candidates_for_complaint(db: Session, complaint_id: str | int) -> list:
    """Find other complaints with same category within 300m."""
    cid = str(complaint_id)
    target = db.query(Complaint).filter(Complaint.id == int(cid) if cid.isdigit() else Complaint.id == cid).first()
    if not target or target.latitude is None or target.longitude is None:
        return []

    others = db.query(Complaint).filter(
        Complaint.id != target.id,
        Complaint.category == target.category,
        Complaint.status.in_(["submitted", "assigned", "in_progress"]),
    ).all()

    candidates = []
    for other in others:
        if other.latitude is None or other.longitude is None:
            continue
        dist = _haversine(target.latitude, target.longitude, other.latitude, other.longitude)
        if dist <= 300.0:  # within 300 meters
            candidates.append({
                "id": f"{target.id}_{other.id}",
                "complaint_id": str(target.id),
                "candidate_complaint_id": str(other.id),
                "similarity": round(max(0.70, 0.95 - (dist / 1000.0)), 2),
                "distance_m": round(dist),
                "reason": f"Same issue ({target.category.value if hasattr(target.category, 'value') else target.category}) located {round(dist)}m away",
                "created_at": other.created_at.isoformat() if hasattr(other.created_at, "isoformat") else str(other.created_at),
            })
    return candidates


def list_duplicate_candidates(db: Session, *, status: str = "pending", limit: int = 50, offset: int = 0) -> dict:
    """List all candidate duplicate pairs across open complaints."""
    open_complaints = db.query(Complaint).filter(
        Complaint.status.in_(["submitted", "assigned", "in_progress"])
    ).all()

    pairs = []
    seen = set()
    for i in range(len(open_complaints)):
        for j in range(i + 1, len(open_complaints)):
            c1, c2 = open_complaints[i], open_complaints[j]
            if c1.category != c2.category:
                continue
            if c1.latitude is None or c2.latitude is None:
                continue
            dist = _haversine(c1.latitude, c1.longitude, c2.latitude, c2.longitude)
            if dist <= 300.0:
                pair_key = tuple(sorted([c1.id, c2.id]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    sim = round(max(0.70, 0.95 - (dist / 1000.0)), 2)
                    pairs.append({
                        "id": f"{c1.id}_{c2.id}",
                        "complaint_id": str(c1.id),
                        "candidate_complaint_id": str(c2.id),
                        "category": c1.category.value if hasattr(c1.category, "value") else str(c1.category),
                        "similarity": sim,
                        "distance_m": round(dist),
                        "reason": f"{round(dist)}m proximity in {c1.department.name if c1.department else 'same sector'}",
                        "created_at": c2.created_at.isoformat() if hasattr(c2.created_at, "isoformat") else str(c2.created_at),
                    })

    paged = pairs[offset : offset + limit]
    return {"items": paged, "total": len(pairs)}


def confirm_merge(db: Session, candidate_id: str, officer_id: str | int) -> dict:
    """Merge the two candidate complaints into one."""
    parts = candidate_id.split("_")
    if len(parts) != 2:
        return {"status": "error", "message": "Invalid candidate id"}

    c1_id, c2_id = int(parts[0]), int(parts[1])
    c1 = db.query(Complaint).filter(Complaint.id == c1_id).first()
    c2 = db.query(Complaint).filter(Complaint.id == c2_id).first()
    if not c1 or not c2:
        return {"status": "error", "message": "Complaint not found"}

    # Target is c1, source is c2
    # Reassign reports of c2 to c1
    db.query(Report).filter(Report.complaint_id == c2.id).update({"complaint_id": c1.id})
    c1.report_count = (c1.report_count or 1) + (c2.report_count or 1)
    c1.priority_score = min(100.0, (c1.priority_score or 30.0) + 15.0)
    c2.status = "resolved"  # close duplicate

    db.add(
        StatusHistory(
            complaint_id=c1.id,
            status=c1.status,
            changed_by_id=int(officer_id) if str(officer_id).isdigit() else None,
            note=f"Merged duplicate complaint #{c2.id} into this case.",
        )
    )
    db.commit()
    return {"status": "merged", "primary_complaint_id": str(c1.id), "merged_complaint_id": str(c2.id)}


def reject_merge(db: Session, candidate_id: str, officer_id: str | int) -> dict:
    """Dismiss candidate duplicate pair."""
    return {"status": "rejected", "candidate_id": candidate_id}


def split_complaint(db: Session, complaint_id: str | int, report_ids: List[str | int], officer_id: str | int, reason: Optional[str] = None) -> dict:
    """Split specific reports off into a separate new complaint."""
    cid = int(complaint_id) if str(complaint_id).isdigit() else complaint_id
    orig = db.query(Complaint).filter(Complaint.id == cid).first()
    if not orig:
        raise ValueError("Complaint not found")

    r_ids = [int(r) if str(r).isdigit() else r for r in report_ids]
    reports_to_move = db.query(Report).filter(Report.id.in_(r_ids), Report.complaint_id == orig.id).all()
    if not reports_to_move or len(reports_to_move) >= (orig.report_count or len(orig.reports)):
        raise ValueError("Cannot move all reports away from the original complaint.")

    primary_moved = reports_to_move[0]
    new_comp = Complaint(
        category=orig.category,
        department_id=orig.department_id,
        latitude=primary_moved.latitude,
        longitude=primary_moved.longitude,
        location_accuracy_m=primary_moved.location_accuracy_m,
        status="submitted",
        priority_score=40.0,
        priority_level=orig.priority_level,
        priority_explanation=f"Split from #{orig.id}: {reason or 'Separate civic issue'}",
        report_count=len(reports_to_move),
        before_photo_path=primary_moved.image_path,
    )
    new_comp.issue_type = orig.category.value if hasattr(orig.category, "value") else str(orig.category)
    new_comp.priority_band = "MEDIUM"
    db.add(new_comp)
    db.flush()

    for r in reports_to_move:
        r.complaint_id = new_comp.id

    orig.report_count = max(1, (orig.report_count or len(reports_to_move)) - len(reports_to_move))

    db.add(
        StatusHistory(
            complaint_id=orig.id,
            status=orig.status,
            changed_by_id=int(officer_id) if str(officer_id).isdigit() else None,
            note=f"Split {len(reports_to_move)} report(s) into new complaint #{new_comp.id}. Reason: {reason or 'Distinct issue'}",
        )
    )
    db.add(
        StatusHistory(
            complaint_id=new_comp.id,
            status="submitted",
            changed_by_id=int(officer_id) if str(officer_id).isdigit() else None,
            note=f"Created via split from complaint #{orig.id}.",
        )
    )
    db.commit()
    return {"new_complaint_id": str(new_comp.id), "original_complaint_id": str(orig.id), "moved_reports": len(reports_to_move)}
