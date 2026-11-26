"""Fills the database with starter data.

Run by hand with:   python -m app.db.seed
It is safe to run many times: it never creates the same record twice.

- Departments are always created (the app needs them).
- Demo users and demo complaints are created only when SEED_DEMO_DATA=true.
  ALL DEMO DATA IS FAKE. Do not use these accounts or passwords in real life.
"""
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.geo import make_point
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Complaint, Department, Report, StatusHistory, User
from app.models.enums import (
    ComplaintCategory,
    ComplaintStatus,
    DuplicateStatus,
    PriorityLevel,
    UserRole,
)

DEPARTMENTS = [
    ("roads", "Roads", "Potholes and damaged roads"),
    ("sanitation", "Sanitation", "Garbage and waste collection"),
    ("electrical", "Electrical", "Streetlights and public lighting"),
    ("drainage", "Drainage", "Blocked drains and waterlogging"),
]

# (email, full name, role, department code, language)
DEMO_USERS = [
    ("admin@civicpulse.demo", "Demo Admin", UserRole.ADMIN, None, "en"),
    ("officer.roads@civicpulse.demo", "Demo Officer (Roads)", UserRole.OFFICER, "roads", "en"),
    ("officer.sanitation@civicpulse.demo", "Demo Officer (Sanitation)", UserRole.OFFICER, "sanitation", "en"),
    ("officer.electrical@civicpulse.demo", "Demo Officer (Electrical)", UserRole.OFFICER, "electrical", "en"),
    ("officer.drainage@civicpulse.demo", "Demo Officer (Drainage)", UserRole.OFFICER, "drainage", "en"),
    ("citizen@civicpulse.demo", "Demo Citizen", UserRole.CITIZEN, None, "en"),
    ("citizen.hindi@civicpulse.demo", "Demo Citizen (Hindi)", UserRole.CITIZEN, None, "hi"),
]

# Fake complaints placed around one town so the map in Module 5 has something to show.
# (category, dept code, lat, lon, severity, confidence, reports, days ago, location factor, status, text)
DEMO_COMPLAINTS = [
    (ComplaintCategory.POTHOLE, "roads", 27.4925, 77.6735, 3, 0.91, 3, 6, 1.0,
     ComplaintStatus.IN_PROGRESS, "Deep pothole near a school gate."),
    (ComplaintCategory.GARBAGE, "sanitation", 27.4948, 77.6742, 2, 0.88, 2, 3, 0.5,
     ComplaintStatus.ASSIGNED, "Garbage piled up next to the market."),
    (ComplaintCategory.STREETLIGHT, "electrical", 27.4901, 77.6690, 2, 0.84, 1, 9, 0.5,
     ComplaintStatus.SUBMITTED, "Streetlight on the main road has not worked for days."),
    (ComplaintCategory.DRAINAGE, "drainage", 27.4962, 77.6711, 4, 0.93, 2, 2, 1.0,
     ComplaintStatus.ASSIGNED, "Blocked drain near the hospital, water on the road."),
    (ComplaintCategory.POTHOLE, "roads", 27.4890, 77.6780, 2, 0.90, 1, 12, 0.0,
     ComplaintStatus.RESOLVED, "Road surface broken near a crossing."),
    (ComplaintCategory.UNCLASSIFIED, None, 27.4915, 77.6760, None, 0.52, 1, 1, 0.0,
     ComplaintStatus.SUBMITTED, "Photograph is unclear. Needs officer review."),
]

STATUS_ORDER = [
    ComplaintStatus.SUBMITTED,
    ComplaintStatus.ASSIGNED,
    ComplaintStatus.IN_PROGRESS,
    ComplaintStatus.RESOLVED,
]


def _demo_priority(severity, reports, days_pending, location_factor):
    """Same formula as the project README. Module 4 will replace this with the real service."""
    sev = severity or 1
    score = 100 * (
        0.40 * (sev / 4)
        + 0.25 * min(1, math.log(1 + reports) / math.log(21))
        + 0.20 * min(1, days_pending / 14)
        + 0.15 * location_factor
    )
    if score >= 60 or sev == 4:
        level = PriorityLevel.HIGH
    elif score >= 40:
        level = PriorityLevel.MEDIUM
    else:
        level = PriorityLevel.LOW
    return round(score, 1), level


def seed_departments(db: Session) -> dict[str, Department]:
    existing = {d.code: d for d in db.scalars(select(Department))}
    for code, name, description in DEPARTMENTS:
        if code not in existing:
            dept = Department(code=code, name=name, description=description)
            db.add(dept)
            existing[code] = dept
    db.flush()
    return existing


def seed_demo_users(db: Session, departments: dict[str, Department]) -> dict[str, User]:
    users = {u.email: u for u in db.scalars(select(User))}
    for email, name, role, dept_code, language in DEMO_USERS:
        if email in users:
            continue
        user = User(
            full_name=name,
            email=email,
            hashed_password=hash_password(settings.demo_password),
            role=role,
            department_id=departments[dept_code].id if dept_code else None,
            preferred_language=language,
        )
        db.add(user)
        users[email] = user
    db.flush()
    return users


def seed_demo_complaints(db: Session, departments: dict[str, Department], users: dict[str, User]) -> None:
    if db.scalar(select(Complaint.id).limit(1)) is not None:
        return  # complaints already exist, do not add more

    citizens = [users["citizen@civicpulse.demo"], users["citizen.hindi@civicpulse.demo"]]
    now = datetime.now(timezone.utc)

    for (category, dept_code, lat, lon, severity, confidence, report_count, days_ago,
         loc_factor, status, text) in DEMO_COMPLAINTS:
        created = now - timedelta(days=days_ago)
        score, level = _demo_priority(severity, report_count, days_ago, loc_factor)
        dept = departments[dept_code] if dept_code else None
        officer = users[f"officer.{dept_code}@civicpulse.demo"] if dept_code else None
        needs_review = confidence < 0.70

        complaint = Complaint(
            category=category,
            department_id=dept.id if dept else None,
            latitude=lat,
            longitude=lon,
            location_accuracy_m=12.0,
            location=make_point(lat, lon),
            severity=severity,
            ai_confidence=confidence,
            ai_explanation="Demo data. This result was written by the seed script, not by the AI.",
            needs_officer_review=needs_review,
            is_demo_result=True,
            priority_score=score,
            priority_level=level,
            priority_explanation="Demo score from the README formula.",
            report_count=report_count,
            status=status,
            assigned_officer_id=officer.id if officer and status != ComplaintStatus.SUBMITTED else None,
            created_at=created,
            updated_at=created,
            resolved_at=created + timedelta(days=2) if status == ComplaintStatus.RESOLVED else None,
        )
        db.add(complaint)
        db.flush()

        for i in range(report_count):
            db.add(Report(
                complaint_id=complaint.id,
                citizen_id=citizens[i % 2].id,
                description_original=text,
                description_language="en",
                description_english=text,
                latitude=lat,
                longitude=lon,
                location_accuracy_m=12.0,
                location=make_point(lat, lon),
                duplicate_status=DuplicateStatus.NONE if i == 0 else DuplicateStatus.MERGED,
                created_at=created + timedelta(hours=i),
            ))

        # One history row for every step up to the current status.
        for step, step_status in enumerate(STATUS_ORDER[: STATUS_ORDER.index(status) + 1]):
            if step_status == ComplaintStatus.SUBMITTED:
                changed_by, note = citizens[0].id, "Complaint submitted."
            elif step_status == ComplaintStatus.ASSIGNED:
                changed_by, note = None, f"Automatically sent to {dept.name if dept else 'a department'}."
            else:
                changed_by = officer.id if officer else None
                note = "Status updated by officer."
            db.add(StatusHistory(
                complaint_id=complaint.id,
                status=step_status,
                changed_by_id=changed_by,
                note=note,
                created_at=created + timedelta(hours=step * 6),
            ))
    db.flush()


def run() -> None:
    with SessionLocal() as db:
        departments = seed_departments(db)
        if settings.seed_demo_data:
            users = seed_demo_users(db, departments)
            seed_demo_complaints(db, departments, users)
        db.commit()
    print("Seed finished." + (" (demo data included)" if settings.seed_demo_data else ""))


if __name__ == "__main__":
    run()
