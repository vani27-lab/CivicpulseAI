"""Plain dataclasses used between layers (no framework dependencies)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional, Sequence
from uuid import UUID


@dataclass
class AIResult:
    """Module 3 output, normalised. Mirrors the agreed Module 3 contract."""
    issue_type: str
    severity: int
    confidence: float
    reason: str
    detected_language: str = "und"
    original_text: str = ""
    translated_text: str = ""
    needs_review: bool = True
    source: str = "fallback"


@dataclass
class ReportInput:
    """Module 2 output: image + GPS (+ optional pre-created report row)."""
    image_bytes: bytes
    latitude: float
    longitude: float
    description: str = ""
    language: Optional[str] = None
    gps_accuracy: Optional[float] = None
    user_id: Optional[UUID] = None
    image_url: Optional[str] = None
    report_id: Optional[UUID] = None  # set if Module 2 already inserted the report row


@dataclass
class Candidate:
    complaint_id: UUID
    issue_type: str
    status: str
    report_count: int
    created_at: datetime
    latitude: float
    longitude: float


@dataclass
class ComplaintRecord:
    id: UUID
    issue_type: str
    status: str
    report_count: int
    created_at: datetime
    latitude: float
    longitude: float
    department_id: Optional[UUID] = None
    max_severity: Optional[int] = None
    priority_score: Optional[float] = None
    priority_band: Optional[str] = None


@dataclass
class ReportRecord:
    id: UUID
    complaint_id: UUID
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    image_url: Optional[str] = None
    user_id: Optional[UUID] = None
    gps_accuracy: Optional[float] = None
    ai_severity: Optional[int] = None
    ai_confidence: Optional[float] = None


@dataclass
class NewReport:
    complaint_id: UUID
    latitude: float
    longitude: float
    created_at: datetime
    report_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    image_url: Optional[str] = None
    original_description: str = ""
    translated_description: str = ""
    gps_accuracy: Optional[float] = None
    ai_confidence: Optional[float] = None
    ai_severity: Optional[int] = None
    embedding: Optional[Sequence[float]] = None


@dataclass
class PossibleDuplicate:
    complaint_id: UUID
    similarity: Optional[float]
    reason: str


@dataclass
class DuplicateDecision:
    status: str
    target_complaint_id: Optional[UUID] = None
    similarity: Optional[float] = None
    possible: List[PossibleDuplicate] = field(default_factory=list)


@dataclass
class LocationContext:
    factor: float = 0.0
    kind: Optional[str] = None
    name: Optional[str] = None
    distance_m: Optional[float] = None


@dataclass
class PriorityResult:
    score: float
    band: str
    reasons: List[str]
    priority_reason: str
    components: dict
    inputs: dict
