"""Pydantic schemas: the stable Module 3 -> Module 4 contract."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .constants import IssueType


class ClassificationResult(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    issue_type: IssueType
    severity: int = Field(ge=1, le=4)
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    detected_language: str
    original_text: str
    translated_text: str
    needs_review: bool
    source: Literal["live_ai", "saved_demo", "fallback"]
