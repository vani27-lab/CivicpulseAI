from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportOut(BaseModel):
    """What the website gets back after a report is submitted."""

    report_id: int
    complaint_id: int
    complaint_status: str
    description_original: Optional[str]
    description_language: Optional[str]
    used_voice_input: bool
    image_url: Optional[str]
    latitude: float
    longitude: float
    location_accuracy_m: Optional[float]
    location_source: str
    created_at: datetime
