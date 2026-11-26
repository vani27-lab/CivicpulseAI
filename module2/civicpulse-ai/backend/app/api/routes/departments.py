from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.department import Department
from app.schemas.department import DepartmentOut

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentOut])
def list_departments(db: DbSession) -> list[Department]:
    """Public list of the four departments complaints are routed to."""
    return list(db.scalars(select(Department).order_by(Department.name)))
