from datetime import datetime
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geography
from geoalchemy2.elements import WKBElement
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, false, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import DuplicateStatus, enum_type
from app.models.user import User

if TYPE_CHECKING:
    from app.models.complaint import Complaint


class Report(Base):
    """One citizen's submission. Several reports can belong to one Complaint."""

    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_location", "location", postgresql_using="gist"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # If an officer splits a wrongly merged report, this simply points to a new Complaint.
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="CASCADE"), index=True
    )
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # --- What the citizen wrote or said ---
    description_original: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description_language: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)  # en, hi
    description_english: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    used_voice_input: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())

    # --- Photograph ---
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    image_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    image_embedding: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float), nullable=True)

    # --- GPS (always stored together with its accuracy) ---
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_accuracy_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    # --- Duplicate detection result (Module 4) ---
    duplicate_status: Mapped[DuplicateStatus] = mapped_column(
        enum_type(DuplicateStatus),
        default=DuplicateStatus.NONE,
        server_default=DuplicateStatus.NONE.value,
    )
    image_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    complaint: Mapped["Complaint"] = relationship(back_populates="reports")
    citizen: Mapped[User] = relationship()
