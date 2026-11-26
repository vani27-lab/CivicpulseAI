"""Helpers mapping a ClassificationResult onto the assumed `reports` columns."""
from .schemas import ClassificationResult


def report_ai_fields(result: ClassificationResult) -> dict:
    """Values for EXISTING reports columns (no schema change needed)."""
    return {
        "ai_confidence": result.confidence,
        "ai_severity": result.severity,
        "translated_description": result.translated_text,
    }


def report_ai_extension_fields(result: ClassificationResult) -> dict:
    """Values for the OPTIONAL columns in models.AIResultColumnsMixin."""
    return {
        "ai_issue_type": result.issue_type,
        "ai_reason": result.reason,
        "ai_needs_review": result.needs_review,
        "ai_source": result.source,
        "detected_language": result.detected_language,
    }
