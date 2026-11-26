"""Routes: POST /complaints/process, GET /complaints/{id}/priority|duplicates, POST /complaints/{id}/split."""
from typing import Any, Callable, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .domain import ReportInput
from .engine import ComplaintProcessor
from .exceptions import ComplaintNotFound, InvalidGPSError, SplitError
from .schemas import (DuplicatesResponse, PriorityResponse, ProcessResult, SplitRequest, SplitResponse)


def build_router(processor_provider: Callable[..., ComplaintProcessor],
                 user_dependency: Optional[Callable[..., Any]] = None,
                 officer_dependency: Optional[Callable[..., Any]] = None) -> APIRouter:
    """
    processor_provider: FastAPI dependency returning a ComplaintProcessor bound to the request's DB session.
    user_dependency:    Module 1 JWT dependency; the returned object's `.id` becomes reports.user_id.
    officer_dependency: Module 1 JWT dependency returning an object with `.id` and `.role`.
                        If omitted the split endpoint is DISABLED (fails closed with 503).
    """
    router = APIRouter(prefix="/complaints", tags=["complaints"])
    _user = user_dependency or (lambda: None)

    async def _no_officer():
        raise HTTPException(503, "Officer authentication is not configured; split is disabled")

    _officer = officer_dependency or _no_officer

    @router.post("/process", response_model=ProcessResult)
    def process(image: UploadFile = File(...), latitude: float = Form(...), longitude: float = Form(...),
                description: str = Form(""), language: Optional[str] = Form(None),
                gps_accuracy: Optional[float] = Form(None), image_url: Optional[str] = Form(None),
                report_id: Optional[UUID] = Form(None),
                proc: ComplaintProcessor = Depends(processor_provider), user: Any = Depends(_user)) -> ProcessResult:
        limit = proc.settings.max_image_bytes
        data = image.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(413, f"Image exceeds {limit} bytes")
        try:
            return proc.process_report(ReportInput(
                image_bytes=data, latitude=latitude, longitude=longitude, description=description,
                language=language, gps_accuracy=gps_accuracy, image_url=image_url, report_id=report_id,
                user_id=getattr(user, "id", None)))
        except InvalidGPSError as exc:
            raise HTTPException(422, str(exc))

    @router.get("/{complaint_id}/priority", response_model=PriorityResponse)
    def priority(complaint_id: UUID, proc: ComplaintProcessor = Depends(processor_provider)) -> PriorityResponse:
        try:
            return proc.get_priority(complaint_id)
        except ComplaintNotFound:
            raise HTTPException(404, "Complaint not found")

    @router.get("/{complaint_id}/duplicates", response_model=DuplicatesResponse)
    def duplicates(complaint_id: UUID, proc: ComplaintProcessor = Depends(processor_provider)) -> DuplicatesResponse:
        try:
            return proc.get_duplicates(complaint_id)
        except ComplaintNotFound:
            raise HTTPException(404, "Complaint not found")

    @router.post("/{complaint_id}/split", response_model=SplitResponse)
    def split(complaint_id: UUID, body: SplitRequest, proc: ComplaintProcessor = Depends(processor_provider),
              officer: Any = Depends(_officer)) -> SplitResponse:
        role = getattr(officer, "role", None)
        if role not in proc.settings.officer_roles:
            raise HTTPException(403, "Officer role required")
        try:
            return proc.split_complaint(complaint_id, body.report_ids, getattr(officer, "id", None), body.comment)
        except ComplaintNotFound:
            raise HTTPException(404, "Complaint not found")
        except SplitError as exc:
            raise HTTPException(409, str(exc))

    return router
