"""OPTIONAL SQLAlchemy extension. NOT applied automatically; no tables are created here.

The agreed `reports` schema has no place for issue_type, reason, needs_review, source
or detected_language. If the team wants them persisted, add this mixin to the Report
model in Module 1 (plus a migration). Without it, Module 4 keeps these values in memory
for the processing request and stores confidence/severity/translation on `reports`.
"""
from sqlalchemy import Boolean, Column, String, Text


class AIResultColumnsMixin:
    ai_issue_type = Column(String(32), nullable=True)
    ai_reason = Column(Text, nullable=True)
    ai_needs_review = Column(Boolean, nullable=False, default=False, server_default="false")
    ai_source = Column(String(16), nullable=True)
    detected_language = Column(String(8), nullable=True)
