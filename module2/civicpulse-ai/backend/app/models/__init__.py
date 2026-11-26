"""Importing this package registers every table with SQLAlchemy/Alembic."""
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.report import Report
from app.models.status_history import StatusHistory
from app.models.user import User

__all__ = ["Complaint", "Department", "Report", "StatusHistory", "User"]
