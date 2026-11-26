from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ComplaintStatus, enum_type
from app.models.user import User

if TYPE_CHECKING:
    from app.models.complaint import Complaint


class StatusHistory(Base):
    """One row for EVERY status change (project rule 10). Never delete these rows."""

    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ComplaintStatus] = mapped_column(enum_type(ComplaintStatus))
    # Who made the change. Empty when the system did it (for example, automatic routing).
    changed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    photo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    complaint: Mapped["Complaint"] = relationship(back_populates="history")
    changed_by: Mapped[Optional[User]] = relationship()
