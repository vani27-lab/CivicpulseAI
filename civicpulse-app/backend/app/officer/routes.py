"""HTTP layer for Module 5. Mounted by ``include_module5_routers(app)``.

Route map (see docs/API_CONTRACT.md):
    GET   /officer/dashboard/stats
    GET   /officer/filters
    GET   /officer/complaints
    GET   /officer/complaints/duplicates      (adapter -> Module 4)
    GET   /officer/complaints/map
    GET   /officer/complaints/{id}
    POST  /officer/duplicates/{candidate_id}/confirm   (adapter -> Module 4)
    POST  /officer/duplicates/{candidate_id}/reject    (adapter -> Module 4)
    PATCH /complaints/{id}/status             (multipart; optional after_photo)
    PATCH /complaints/{id}/classification
    POST  /complaints/{id}/split              (adapter -> Module 4)
    GET   /stats/heatmap

Static paths are declared before ``/officer/complaints/{id}`` on purpose.
"""
from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from . import duplicates_gateway, integration, services
from .config import get_settings
from .errors import ServiceError
from .queries import ComplaintFilters
from .schemas import (
    ClassificationIn,
    ClassificationOut,
    ComplaintDetailOut,
    ComplaintId,
    ComplaintListOut,
    FilterOptionsOut,
    HeatmapOut,
    MapPoint,
    SplitIn,
    StatsOut,
    StatusUpdateOut,
)
from .security import is_admin, require_officer
from .uploads import LocalStorage, validate_image

officer_router = APIRouter(prefix="/officer", tags=["officer"], dependencies=[Depends(require_officer)])
actions_router = APIRouter(prefix="/complaints", tags=["officer-actions"], dependencies=[Depends(require_officer)])
stats_router = APIRouter(prefix="/stats", tags=["officer-stats"], dependencies=[Depends(require_officer)])
duplicates_router = APIRouter(prefix="/officer", tags=["officer-duplicates"], dependencies=[Depends(require_officer)])


def _filters(
    q: str | None = Query(None, max_length=120),
    department_id: str | None = None,
    issue_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    active_only: bool = False,
) -> ComplaintFilters:
    return ComplaintFilters(
        q=q,
        department_id=department_id,
        issue_type=issue_type,
        priority_band=priority,
        status=status,
        date_from=date_from,
        date_to=date_to,
        active_only=active_only,
    )


@officer_router.get("/dashboard/stats", response_model=StatsOut)
def dashboard_stats(db=Depends(integration.get_db)):
    return services.get_stats(db)


@officer_router.get("/filters", response_model=FilterOptionsOut)
def filter_options(db=Depends(integration.get_db)):
    return services.get_filter_options(db)


@officer_router.get("/complaints", response_model=ComplaintListOut)
def list_complaints(
    filters: ComplaintFilters = Depends(_filters),
    sort_by: str = "priority",
    sort_dir: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(integration.get_db),
):
    return services.list_complaints(db, filters, sort_by, sort_dir, page, page_size)


@duplicates_router.get("/complaints/duplicates")
def list_duplicates(
    status: str = "pending",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(integration.get_db),
):
    return duplicates_gateway.list_candidates(db, status=status, limit=page_size, offset=(page - 1) * page_size)


@officer_router.get("/complaints/map", response_model=list[MapPoint])
def complaint_map(filters: ComplaintFilters = Depends(_filters), db=Depends(integration.get_db)):
    return services.get_map_points(db, filters)


@officer_router.get("/complaints/{complaint_id}", response_model=ComplaintDetailOut)
def complaint_detail(complaint_id: ComplaintId, user=Depends(require_officer), db=Depends(integration.get_db)):
    return services.get_complaint_detail(db, complaint_id, role_is_admin=is_admin(user), settings=get_settings())


@duplicates_router.post("/duplicates/{candidate_id}/confirm")
def confirm_merge(candidate_id: str, user=Depends(require_officer), db=Depends(integration.get_db)):
    return duplicates_gateway.confirm_merge(db, candidate_id, integration.user_id(user))


@duplicates_router.post("/duplicates/{candidate_id}/reject")
def reject_merge(candidate_id: str, user=Depends(require_officer), db=Depends(integration.get_db)):
    return duplicates_gateway.reject_merge(db, candidate_id, integration.user_id(user))


@actions_router.patch("/{complaint_id}/status", response_model=StatusUpdateOut)
async def update_status(
    complaint_id: ComplaintId,
    new_status: str = Form(...),
    comment: str | None = Form(None, max_length=1000),
    admin_override: bool = Form(False),
    override_reason: str | None = Form(None, max_length=500),
    after_photo: UploadFile | None = File(None),
    user=Depends(require_officer),
    db=Depends(integration.get_db),
):
    settings = get_settings()
    photo = None
    if after_photo is not None and after_photo.filename:
        raw = await after_photo.read(settings.max_upload_bytes + 1)
        photo = validate_image(raw, settings.max_upload_bytes)  # raises UploadError

    storage = LocalStorage(settings.upload_dir, settings.media_base_url)

    def work():
        return services.update_status(
            db,
            complaint_id=complaint_id,
            officer_id=integration.user_id(user),
            role_is_admin=is_admin(user),
            new_status_raw=new_status,
            comment=comment,
            photo=photo,
            admin_override=admin_override,
            override_reason=override_reason,
            storage=storage,
            settings=settings,
        )

    return await run_in_threadpool(work)


@actions_router.patch("/{complaint_id}/classification", response_model=ClassificationOut)
def update_classification(
    complaint_id: ComplaintId,
    body: ClassificationIn,
    user=Depends(require_officer),
    db=Depends(integration.get_db),
):
    return services.correct_classification(
        db,
        complaint_id=complaint_id,
        officer_id=integration.user_id(user),
        new_issue_type=body.issue_type,
        reason=body.reason,
    )


@actions_router.post("/{complaint_id}/split")
def split_complaint(
    complaint_id: ComplaintId, body: SplitIn, user=Depends(require_officer), db=Depends(integration.get_db)
):
    return duplicates_gateway.split_complaint(
        db, str(complaint_id), [str(r) for r in body.report_ids], integration.user_id(user), body.reason
    )


@stats_router.get("/heatmap", response_model=HeatmapOut)
def heatmap(filters: ComplaintFilters = Depends(_filters), db=Depends(integration.get_db)):
    if not filters.status:
        filters.active_only = True  # density of open work; resolved issues no longer need attention
    return services.get_heatmap(db, filters)


async def _service_error_handler(_request: Request, exc: ServiceError):
    return JSONResponse(
        status_code=exc.status_code, content={"detail": {"code": exc.code, "message": exc.message}}
    )


def register(app) -> None:
    settings = get_settings()
    app.add_exception_handler(ServiceError, _service_error_handler)
    if settings.mount_duplicate_routes:
        app.include_router(duplicates_router)  # first: static /officer/complaints/duplicates beats {id}
    app.include_router(officer_router)
    app.include_router(actions_router)
    if settings.mount_heatmap:
        app.include_router(stats_router)
