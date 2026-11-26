"""Creating a report (one citizen submission) together with its complaint.

Integrated with:
- Module 3: AI Intelligence Engine (classify_complaint)
- Module 4: Complaint Intelligence Engine (priority calculation, department routing, duplicate detection)
"""
from pathlib import Path
from typing import Optional
import json
import math

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.geo import make_point
from app.models import Complaint, Department, Report, StatusHistory, User
from app.models.enums import (
    ComplaintCategory,
    ComplaintStatus,
    DuplicateStatus,
    LocationSource,
    PriorityLevel,
)
from app.services.storage import SavedImage


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def create_report(
    db: Session,
    citizen: User,
    *,
    image: SavedImage,
    description: str,
    language: str,
    used_voice_input: bool,
    latitude: float,
    longitude: float,
    accuracy_m: Optional[float],
    location_source: LocationSource,
) -> tuple[Report, Complaint]:
    # 1. AI Intelligence Engine (Module 3)
    ai_res = None
    try:
        from app.modules.ai_engine.service import classify_complaint
        img_bytes = (Path(settings.upload_dir) / image.relative_path).read_bytes()
        ai_res = classify_complaint(img_bytes, description, language)
    except Exception:
        ai_res = None

    # If Vision AI is unavailable or returned unclassified, use description keyword heuristic
    if not ai_res or str(ai_res.issue_type).lower() in ("unclassified", "other") or (ai_res.confidence or 0.0) == 0.0:
        from app.modules.ai_engine.constants import IssueType, SOURCE_FALLBACK
        desc_lower = (description or "").lower()
        if any(w in desc_lower for w in ["pothole", "road", "crater", "asphalt", "गड्ढा", "सड़क"]):
            fallback_type = IssueType.POTHOLE
            sev = 3
            conf = 0.85
            reason = "Keyword heuristic: identified pothole / road damage from description (Vision AI fallback)"
        elif any(w in desc_lower for w in ["garbage", "trash", "waste", "dump", "कचरा", "कूड़ा"]):
            fallback_type = IssueType.GARBAGE
            sev = 2
            conf = 0.85
            reason = "Keyword heuristic: identified garbage / sanitation issue from description (Vision AI fallback)"
        elif any(w in desc_lower for w in ["streetlight", "light", "lamp", "dark", "बिजली", "बत्ती"]):
            fallback_type = IssueType.BROKEN_STREETLIGHT
            sev = 2
            conf = 0.85
            reason = "Keyword heuristic: identified streetlight / electrical issue from description (Vision AI fallback)"
        elif any(w in desc_lower for w in ["drain", "water", "sewage", "overflow", "नाली", "पानी", "सीवर"]):
            fallback_type = IssueType.BLOCKED_DRAIN
            sev = 3
            conf = 0.85
            reason = "Keyword heuristic: identified drainage / water issue from description (Vision AI fallback)"
        else:
            fallback_type = IssueType.UNCLASSIFIED
            sev = 1
            conf = 0.0
            reason = ai_res.reason if ai_res else "Manual review needed"

        from app.modules.ai_engine.schemas import ClassificationResult
        ai_res = ClassificationResult(
            issue_type=fallback_type,
            severity=sev,
            confidence=conf,
            reason=reason,
            detected_language=language or "en",
            original_text=description,
            translated_text=description if language == "en" else (ai_res.translated_text if ai_res else ""),
            needs_review=(fallback_type == IssueType.UNCLASSIFIED),
            source=SOURCE_FALLBACK,
        )

    # 2. Map issue type to ComplaintCategory
    category_map = {
        "pothole": ComplaintCategory.POTHOLE,
        "road_damage": ComplaintCategory.POTHOLE,
        "garbage": ComplaintCategory.GARBAGE,
        "broken_streetlight": ComplaintCategory.STREETLIGHT,
        "streetlight": ComplaintCategory.STREETLIGHT,
        "blocked_drain": ComplaintCategory.DRAINAGE,
        "drainage": ComplaintCategory.DRAINAGE,
        "other": ComplaintCategory.OTHER,
        "unclassified": ComplaintCategory.UNCLASSIFIED,
    }
    cat = category_map.get(str(ai_res.issue_type).lower(), ComplaintCategory.UNCLASSIFIED)

    # 3. Department Routing (Module 4)
    dept_code_map = {
        ComplaintCategory.POTHOLE: "roads",
        ComplaintCategory.GARBAGE: "sanitation",
        ComplaintCategory.STREETLIGHT: "electrical",
        ComplaintCategory.DRAINAGE: "drainage",
    }
    dept_code = dept_code_map.get(cat)
    dept = db.query(Department).filter(Department.code == dept_code).first() if dept_code else None

    # 4. Check for Candidate Duplicate Complaints (Module 4 - 50m radius)
    candidate_complaint: Optional[Complaint] = None
    if cat != ComplaintCategory.UNCLASSIFIED:
        open_complaints = db.query(Complaint).filter(
            Complaint.category == cat,
            Complaint.status.in_([ComplaintStatus.SUBMITTED, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS]),
        ).all()
        for comp in open_complaints:
            dist = _haversine_distance_m(latitude, longitude, comp.latitude, comp.longitude)
            if dist <= 50.0:
                candidate_complaint = comp
                break

    # 5. Geospatial Intelligence & Nearby Facility Detection
    from app.modules.complaint_engine.domain import LocationContext
    loc_ctx = LocationContext(factor=0.0, kind=None)
    try:
        from app.services.geo_facility_service import analyze_geospatial_impact
        geo_res = analyze_geospatial_impact(
            lat=latitude,
            lon=longitude,
            issue_type=cat.value,
            severity=max(ai_res.severity or 1, (candidate_complaint.severity or 1) if candidate_complaint else 1),
            db=db,
        )
        nearest_fac = geo_res.nearest_facility
        loc_ctx = LocationContext(
            factor=geo_res.location_factor,
            kind=nearest_fac.facility_type if nearest_fac else None,
            name=nearest_fac.name if nearest_fac else None,
            distance_m=nearest_fac.distance_m if nearest_fac else None,
            is_emergency=geo_res.is_emergency,
            nearby_facilities=[
                {"name": f.name, "type": f.facility_type, "distance_m": f.distance_m, "lat": f.latitude, "lon": f.longitude}
                for f in geo_res.nearby_facilities
            ],
            impact_explanation=geo_res.impact_explanation,
            citizen_urgency_reason=geo_res.citizen_urgency_reason,
        )
    except Exception as e:
        logger.warning("Geospatial analysis fallback: %s", e)

    # 6. Priority Calculation (Module 4)
    rep_count = (candidate_complaint.report_count + 1) if candidate_complaint else 1
    sev_level = max(ai_res.severity or 1, (candidate_complaint.severity or 1) if candidate_complaint else 1)
    try:
        from app.modules.complaint_engine.priority import calculate_priority
        p_res = calculate_priority(
            severity=sev_level,
            reports=rep_count,
            days_pending=0,
            location=loc_ctx,
            issue_type=cat.value,
        )
        p_score = p_res.score
        p_band_str = p_res.band.lower()
        p_expl = p_res.priority_reason
    except Exception as e:
        logger.warning("Priority calculation fallback: %s", e)
        p_score = 30.0 + (rep_count * 10.0)
        p_band_str = "medium" if p_score >= 40 else "low"
        p_expl = f"Calculated priority score {p_score}"

    if p_band_str == "critical":
        priority_enum = PriorityLevel.CRITICAL
    elif p_band_str == "high":
        priority_enum = PriorityLevel.HIGH
    elif p_band_str == "medium":
        priority_enum = PriorityLevel.MEDIUM
    else:
        priority_enum = PriorityLevel.LOW

    if candidate_complaint:
        # Merge into existing complaint
        complaint = candidate_complaint
        complaint.report_count = rep_count
        complaint.priority_score = p_score
        complaint.priority_level = priority_enum
        complaint.priority_explanation = p_expl
        complaint.issue_type = cat.value
        complaint.priority_band = p_band_str.upper()
        complaint.priority_reason = p_expl
        complaint.nearest_facility_name = loc_ctx.name
        complaint.nearest_facility_type = loc_ctx.kind
        complaint.nearest_facility_distance_m = loc_ctx.distance_m
        complaint.nearby_facilities_json = json.dumps(loc_ctx.nearby_facilities) if getattr(loc_ctx, "nearby_facilities", None) else None
        complaint.citizen_urgency_reason = loc_ctx.citizen_urgency_reason
        complaint.is_emergency = loc_ctx.is_emergency
        duplicate_status = DuplicateStatus.MERGED
    else:
        # Create new complaint
        complaint = Complaint(
            category=cat,
            department_id=dept.id if dept else None,
            latitude=latitude,
            longitude=longitude,
            location_accuracy_m=accuracy_m,
            location=make_point(latitude, longitude),
            severity=ai_res.severity,
            ai_confidence=ai_res.confidence,
            ai_explanation=ai_res.reason,
            needs_officer_review=ai_res.needs_review,
            is_demo_result=(ai_res.source != "live_ai"),
            priority_score=p_score,
            priority_level=priority_enum,
            priority_explanation=p_expl,
            report_count=1,
            status=ComplaintStatus.SUBMITTED,
            image_sha256=image.sha256,
            before_photo_path=image.relative_path,
        )
        complaint.issue_type = cat.value
        complaint.priority_band = p_band_str.upper()
        complaint.priority_reason = p_expl
        complaint.nearest_facility_name = loc_ctx.name
        complaint.nearest_facility_type = loc_ctx.kind
        complaint.nearest_facility_distance_m = loc_ctx.distance_m
        complaint.nearby_facilities_json = json.dumps(loc_ctx.nearby_facilities) if getattr(loc_ctx, "nearby_facilities", None) else None
        complaint.citizen_urgency_reason = loc_ctx.citizen_urgency_reason
        complaint.is_emergency = loc_ctx.is_emergency
        db.add(complaint)
        db.flush()
        duplicate_status = DuplicateStatus.NONE

    # Create Report
    report = Report(
        complaint_id=complaint.id,
        citizen_id=citizen.id,
        description_original=description,
        description_language=language,
        description_english=ai_res.translated_text or (description if language == "en" else description),
        used_voice_input=used_voice_input,
        image_path=image.relative_path,
        image_sha256=image.sha256,
        latitude=latitude,
        longitude=longitude,
        location_accuracy_m=accuracy_m,
        location_source=location_source,
        location=make_point(latitude, longitude),
        duplicate_status=duplicate_status,
    )
    report.user_id = citizen.id
    report.image_url = image.relative_path
    report.original_description = description
    report.translated_description = report.description_english
    db.add(report)

    # Add StatusHistory
    db.add(
        StatusHistory(
            complaint_id=complaint.id,
            status=ComplaintStatus.SUBMITTED,
            changed_by_id=citizen.id,
            note="Complaint submitted (AI Classified: " + cat.value + ").",
            photo_path=image.relative_path,
        )
    )

    db.commit()
    db.refresh(report)
    db.refresh(complaint)
    return report, complaint
