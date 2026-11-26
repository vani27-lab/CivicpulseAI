"""Creating a report (one citizen submission) together with its complaint.

Integrated with:
- Module 3: AI Intelligence Engine (classify_complaint)
- Module 4: Complaint Intelligence Engine (priority calculation, department routing, duplicate detection)
"""
from pathlib import Path
from typing import Optional
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
    try:
        from app.modules.ai_engine.service import classify_complaint
        img_bytes = (Path(settings.upload_dir) / image.relative_path).read_bytes()
        ai_res = classify_complaint(img_bytes, description, language)
    except Exception as e:
        from app.modules.ai_engine.schemas import ClassificationResult
        # Intelligent fallback based on description keywords if vision API is unconfigured
        desc_lower = (description or "").lower()
        if "pothole" in desc_lower or "road" in desc_lower:
            fallback_type = "pothole"
            sev = 3
        elif "garbage" in desc_lower or "trash" in desc_lower or "waste" in desc_lower:
            fallback_type = "garbage"
            sev = 2
        elif "light" in desc_lower or "street" in desc_lower or "dark" in desc_lower:
            fallback_type = "streetlight"
            sev = 2
        elif "drain" in desc_lower or "water" in desc_lower or "sewage" in desc_lower:
            fallback_type = "drainage"
            sev = 3
        else:
            fallback_type = "unclassified"
            sev = 1

        ai_res = ClassificationResult(
            issue_type=fallback_type,
            severity=sev,
            confidence=0.85 if fallback_type != "unclassified" else 0.0,
            reason=f"Keyword heuristic: identified {fallback_type}" if fallback_type != "unclassified" else "Manual review needed",
            detected_language=language or "en",
            original_text=description,
            translated_text=description if language == "en" else "",
            needs_review=(fallback_type == "unclassified"),
            source="demo_fallback",
        )

    # 2. Map issue type to ComplaintCategory
    category_map = {
        "pothole": ComplaintCategory.POTHOLE,
        "garbage": ComplaintCategory.GARBAGE,
        "streetlight": ComplaintCategory.STREETLIGHT,
        "drainage": ComplaintCategory.DRAINAGE,
        "other": ComplaintCategory.OTHER,
        "unclassified": ComplaintCategory.UNCLASSIFIED,
    }
    cat = category_map.get(ai_res.issue_type.lower(), ComplaintCategory.UNCLASSIFIED)

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

    # 5. Priority Calculation (Module 4)
    rep_count = (candidate_complaint.report_count + 1) if candidate_complaint else 1
    sev_level = max(ai_res.severity or 1, (candidate_complaint.severity or 1) if candidate_complaint else 1)
    try:
        from app.modules.complaint_engine.priority import calculate_priority
        from app.modules.complaint_engine.domain import LocationContext
        p_res = calculate_priority(
            severity=sev_level,
            reports=rep_count,
            days_pending=0,
            location=LocationContext(factor=0.0, kind=None),
            issue_type=cat.value,
        )
        p_score = p_res.score
        p_band_str = p_res.band.lower()
        p_expl = p_res.priority_reason
    except Exception:
        p_score = 30.0 + (rep_count * 10.0)
        p_band_str = "medium" if p_score >= 40 else "low"
        p_expl = f"Calculated priority score {p_score}"

    priority_enum = PriorityLevel.HIGH if p_band_str == "high" else (PriorityLevel.MEDIUM if p_band_str == "medium" else PriorityLevel.LOW)

    if candidate_complaint:
        # Merge into existing complaint
        complaint = candidate_complaint
        complaint.report_count = rep_count
        complaint.priority_score = p_score
        complaint.priority_level = priority_enum
        complaint.priority_explanation = p_expl
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
