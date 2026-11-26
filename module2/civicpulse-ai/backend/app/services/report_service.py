"""Creating a report (one citizen submission) together with its complaint.

MODULE 2 BEHAVIOUR (simple on purpose):
  every report creates a NEW complaint, category "unclassified", flagged for officer review.

HOOKS for later modules (search for "TODO Module"):
  Module 3 -> classify the photo, fill category / severity / confidence / translation
  Module 4 -> find duplicates (attach to an existing complaint instead of creating one),
              calculate priority, route to a department
Invalid or missing AI output must never block submission (project rule 7), so the report is
saved FIRST and the later modules only improve it.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.geo import make_point
from app.models import Complaint, Report, StatusHistory, User
from app.models.enums import ComplaintCategory, ComplaintStatus, LocationSource
from app.services.storage import SavedImage


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
    complaint = Complaint(
        category=ComplaintCategory.UNCLASSIFIED,  # TODO Module 3: real AI classification
        latitude=latitude,
        longitude=longitude,
        location_accuracy_m=accuracy_m,
        location=make_point(latitude, longitude),
        needs_officer_review=True,  # unclassified => an officer must look at it
        status=ComplaintStatus.SUBMITTED,
        report_count=1,  # TODO Module 4: duplicate detection may merge into an existing complaint
        image_sha256=image.sha256,
        before_photo_path=image.relative_path,
        # TODO Module 4: priority_score / priority_level / department_id
    )
    db.add(complaint)
    db.flush()  # gives the complaint its id

    report = Report(
        complaint_id=complaint.id,
        citizen_id=citizen.id,
        description_original=description,
        description_language=language,
        # TODO Module 3: translate Hindi to English. Until then only English text is copied.
        description_english=description if language == "en" else None,
        used_voice_input=used_voice_input,
        image_path=image.relative_path,
        image_sha256=image.sha256,
        latitude=latitude,
        longitude=longitude,
        location_accuracy_m=accuracy_m,
        location_source=location_source,
        location=make_point(latitude, longitude),
    )
    db.add(report)

    # Project rule 10: every status change is recorded.
    db.add(
        StatusHistory(
            complaint_id=complaint.id,
            status=ComplaintStatus.SUBMITTED,
            changed_by_id=citizen.id,
            note="Complaint submitted.",
            photo_path=image.relative_path,
        )
    )
    db.commit()
    db.refresh(report)
    db.refresh(complaint)
    return report, complaint
