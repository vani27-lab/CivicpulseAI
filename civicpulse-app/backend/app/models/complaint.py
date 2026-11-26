from datetime import datetime
from typing import Optional

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.department import Department
from app.models.enums import ComplaintCategory, ComplaintStatus, PriorityLevel, enum_type
from app.models.user import User


class Complaint(Base):
    """ONE real-world problem (for example, one pothole).

    If five citizens report the same pothole, there is one Complaint and five
    Reports. Complaint = the problem. Report = one citizen's submission.
    """

    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_location", "location", postgresql_using="gist"),
        Index("ix_complaints_category_status", "category", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    # --- What and where ---
    category: Mapped[ComplaintCategory] = mapped_column(
        enum_type(ComplaintCategory),
        default=ComplaintCategory.UNCLASSIFIED,
        server_default=ComplaintCategory.UNCLASSIFIED.value,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_accuracy_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    # PostGIS copy of the same point, used for distance searches (Module 4).
    location: Mapped[Optional[WKBElement]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False).with_variant(Text, "sqlite"),
        nullable=True,
    )

    # --- AI result (Module 3) ---
    severity: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)  # 1 to 4
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    needs_officer_review: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )
    is_demo_result: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    # --- Priority (Module 4) ---
    priority_score: Mapped[float] = mapped_column(Float, default=0, server_default="0")
    priority_level: Mapped[PriorityLevel] = mapped_column(
        enum_type(PriorityLevel), default=PriorityLevel.LOW, server_default=PriorityLevel.LOW.value
    )
    priority_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nearest_facility_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nearest_facility_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    nearest_facility_distance_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nearby_facilities_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citizen_urgency_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    report_count: Mapped[int] = mapped_column(Integer, default=1, server_default="1")

    # --- Progress ---
    status: Mapped[ComplaintStatus] = mapped_column(
        enum_type(ComplaintStatus),
        default=ComplaintStatus.SUBMITTED,
        server_default=ComplaintStatus.SUBMITTED.value,
    )
    assigned_officer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    before_photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    after_photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # --- Duplicate detection (Module 4) ---
    image_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    image_embedding: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float).with_variant(Text, "sqlite"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    department: Mapped[Optional[Department]] = relationship()
    assigned_officer: Mapped[Optional[User]] = relationship()
    reports: Mapped[list["Report"]] = relationship(back_populates="complaint")
    history: Mapped[list["StatusHistory"]] = relationship(
        back_populates="complaint", order_by="StatusHistory.created_at"
    )


# Imported at the bottom so the names used in the relationships above exist.
from app.models.report import Report  # noqa: E402
from app.models.status_history import StatusHistory  # noqa: E402
