"""Pydantic API schemas = the stable Module 4 output contract."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProcessResult(BaseModel):
    # --- agreed contract ---
    complaint_id: UUID
    duplicate_status: str            # new | merged | possible_duplicate
    report_count: int
    priority_score: float
    priority_band: str               # HIGH | MEDIUM | LOW
    priority_reason: str
    department_id: Optional[UUID] = None
    # --- additions (documented in README) ---
    report_id: Optional[UUID] = None
    issue_type: str = "unclassified"
    severity: int = 1
    needs_review: bool = True
    ai_source: str = "fallback"
    similarity: Optional[float] = None
    possible_duplicate_ids: List[UUID] = Field(default_factory=list)
    department_name: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class PriorityResponse(BaseModel):
    complaint_id: UUID
    priority_score: float
    priority_band: str
    priority_reason: str
    reasons: List[str]
    components: dict
    inputs: dict
    stored_priority_score: Optional[float] = None
    stored_priority_band: Optional[str] = None
    computed_at: datetime


class MergedReportOut(BaseModel):
    report_id: UUID
    created_at: datetime
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PossibleDuplicateOut(BaseModel):
    complaint_id: UUID
    similarity: Optional[float] = None
    reason: str


class DuplicatesResponse(BaseModel):
    complaint_id: UUID
    report_count: int
    reports: List[MergedReportOut]
    possible_duplicates: List[PossibleDuplicateOut]


class SplitRequest(BaseModel):
    report_ids: List[UUID] = Field(min_length=1)
    comment: Optional[str] = None


class SplitResponse(BaseModel):
    original_complaint_id: UUID
    new_complaint_id: UUID
    moved_report_ids: List[UUID]
    original_report_count: int
    new_report_count: int
    original_priority_score: float
    original_priority_band: str
    new_priority_score: float
    new_priority_band: str
