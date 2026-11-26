"""Pydantic response/request models for the officer API.

ASSUMPTION: identifiers are UUIDs (as stated in the handoff). If Module 1 uses
integers, change ``ComplaintId`` and the ``str`` id fields in one place here."""
import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

ComplaintId = int | str


class StatsOut(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
    high_priority: int


class ComplaintRow(BaseModel):
    id: str
    issue_type: str | None
    status: str | None
    department_id: str | None
    department_name: str | None
    report_count: int
    priority_score: float | None
    priority_band: str | None
    created_at: datetime
    latitude: float | None
    longitude: float | None


class ComplaintListOut(BaseModel):
    items: list[ComplaintRow]
    total: int
    page: int
    page_size: int


class ReportOut(BaseModel):
    id: str
    image_url: str | None
    original_description: str | None
    translated_description: str | None
    latitude: float | None
    longitude: float | None
    gps_accuracy: float | None
    ai_confidence: float | None
    ai_severity: Any | None
    created_at: datetime


class HistoryOut(BaseModel):
    id: str
    old_status: str | None
    new_status: str | None
    officer_id: str | None
    officer_name: str | None
    comment: str | None
    after_photo_url: str | None
    created_at: datetime


class CorrectionOut(BaseModel):
    id: str
    old_issue_type: str | None
    new_issue_type: str
    reason: str | None
    officer_id: str | None
    officer_name: str | None
    created_at: datetime


class PriorityOut(BaseModel):
    score: float | None
    band: str | None
    reasons: list[str]


class AIClassificationOut(BaseModel):
    original_issue_type: str | None
    current_issue_type: str | None
    corrected: bool
    confidence: float | None
    severity: Any | None


class ComplaintDetailOut(BaseModel):
    id: str
    issue_type: str | None
    status: str | None
    department_id: str | None
    department_name: str | None
    report_count: int
    created_at: datetime
    updated_at: datetime | None
    latitude: float | None
    longitude: float | None
    gps_accuracy: float | None
    priority: PriorityOut
    ai_classification: AIClassificationOut
    reports: list[ReportOut]
    history: list[HistoryOut]
    corrections: list[CorrectionOut]
    duplicate_candidates: list[dict]
    allowed_next_statuses: list[str]
    can_override: bool
    before_photo_url: str | None
    after_photo_url: str | None


class StatusUpdateOut(BaseModel):
    complaint_id: str
    old_status: str | None
    new_status: str
    history_id: str
    after_photo_url: str | None
    override_used: bool
    updated_at: datetime


class ClassificationIn(BaseModel):
    issue_type: str = Field(min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=500)


class ClassificationOut(BaseModel):
    complaint_id: str
    old_issue_type: str | None
    new_issue_type: str
    correction_id: str


class SplitIn(BaseModel):
    report_ids: list[int | str] = Field(min_length=1)
    reason: str = Field(min_length=3, max_length=500)


class MapPoint(BaseModel):
    id: str
    issue_type: str | None
    status: str | None
    priority_band: str | None
    priority_score: float | None
    report_count: int
    latitude: float
    longitude: float


class HeatmapOut(BaseModel):
    # each point: [latitude, longitude, weight 0..1]
    points: list[list[float]]
    count: int


class FilterOptionsOut(BaseModel):
    departments: list[dict]
    issue_types: list[str]
    statuses: list[dict]
    priorities: list[str]


class DateRange(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
