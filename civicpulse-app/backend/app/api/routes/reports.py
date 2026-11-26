from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import DbSession, require_roles
from app.models import User
from app.models.enums import LocationSource, UserRole
from app.schemas.report import ReportOut
from app.services import report_service, storage

router = APIRouter(prefix="/reports", tags=["Reports (citizen)"])

Citizen = Annotated[User, Depends(require_roles(UserRole.CITIZEN))]


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def submit_report(
    db: DbSession,
    citizen: Citizen,
    image: Annotated[UploadFile, File(description="Photo of the problem (JPEG, PNG or WebP)")],
    latitude: Annotated[float, Form(ge=-90, le=90)],
    longitude: Annotated[float, Form(ge=-180, le=180)],
    description: Annotated[str, Form(max_length=2000)],
    location_accuracy_m: Annotated[Optional[float], Form(ge=0)] = None,
    location_source: Annotated[Literal["gps", "manual_pin"], Form()] = "gps",
    description_language: Annotated[Literal["en", "hi"], Form()] = "en",
    used_voice_input: Annotated[bool, Form()] = False,
) -> ReportOut:
    """A citizen reports a problem: photo + location + description (typed or spoken).

    Sent as multipart form data (not JSON) because it contains a file.
    """
    text = description.strip()
    if len(text) < 3:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Please describe the problem.")

    saved = storage.save_image(image.file)  # checks type and size, may raise 400/413
    try:
        report, complaint = report_service.create_report(
            db,
            citizen,
            image=saved,
            description=text,
            language=description_language,
            used_voice_input=used_voice_input,
            latitude=latitude,
            longitude=longitude,
            accuracy_m=location_accuracy_m,
            location_source=LocationSource(location_source),
        )
    except Exception:
        db.rollback()
        storage.delete_image(saved.relative_path)  # do not leave orphan photos behind
        raise

    return ReportOut(
        report_id=report.id,
        complaint_id=complaint.id,
        complaint_status=complaint.status.value,
        description_original=report.description_original,
        description_language=report.description_language,
        used_voice_input=report.used_voice_input,
        image_url=f"/uploads/{report.image_path}" if report.image_path else None,
        latitude=report.latitude,
        longitude=report.longitude,
        location_accuracy_m=report.location_accuracy_m,
        location_source=report.location_source.value,
        created_at=report.created_at,
    )
