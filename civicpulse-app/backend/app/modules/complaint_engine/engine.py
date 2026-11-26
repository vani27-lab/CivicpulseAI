"""Orchestrator: New Report -> AI -> GPS -> candidates -> CLIP -> merge/create -> priority -> routing -> save."""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import UUID

from .config import Settings
from .constants import (DUP_MERGED, DUP_NEW, DUP_POSSIBLE, ISSUE_UNCLASSIFIED)
from .domain import (AIResult, DuplicateDecision, NewReport, PossibleDuplicate, PriorityResult, ReportInput)
from .duplicates import best_similarity, decide_duplicate
from .embedder import ImageEmbedder, NullEmbedder
from .exceptions import ComplaintNotFound, SplitError
from .gps import validate_gps
from .places import NullPlaceProvider, PlaceProvider
from .priority import calculate_priority
from .repository import ComplaintRepository
from .routing import resolve_department
from .schemas import (DuplicatesResponse, MergedReportOut, PossibleDuplicateOut, PriorityResponse,
                      ProcessResult, SplitResponse)

logger = logging.getLogger(__name__)

# Module 3 contract: classify_complaint(image_bytes, description, language=None) -> object/dict with AI fields
ClassifierFn = Callable[[bytes, str, Optional[str]], Any]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)


def normalize_ai(raw: Any) -> AIResult:
    """Accept Module 3's ClassificationResult (or a dict with the same keys); never trust blindly."""
    it = _get(raw, "issue_type", ISSUE_UNCLASSIFIED)
    it = str(getattr(it, "value", it))
    sev = _get(raw, "severity", 1)
    conf = _get(raw, "confidence", 0.0)
    if isinstance(sev, bool) or not isinstance(sev, int) or not 1 <= sev <= 4:
        sev = 1
    if isinstance(conf, bool) or not isinstance(conf, (int, float)):
        conf = 0.0
    return AIResult(
        issue_type=it, severity=sev, confidence=float(conf), reason=str(_get(raw, "reason", "") or ""),
        detected_language=str(_get(raw, "detected_language", "und") or "und"),
        original_text=str(_get(raw, "original_text", "") or ""),
        translated_text=str(_get(raw, "translated_text", "") or ""),
        needs_review=bool(_get(raw, "needs_review", True)), source=str(_get(raw, "source", "fallback")))


def default_classifier() -> ClassifierFn:
    """Late import of Module 3 so Module 4 can be developed and tested without it."""
    try:
        from app.modules.ai_engine import classify_complaint  # Module 3 package path (adjust if needed)
    except ImportError as exc:
        raise RuntimeError("Module 3 (ai_engine) not importable. Pass classifier=... to ComplaintProcessor "
                           "or adjust default_classifier().") from exc
    return classify_complaint


class ComplaintProcessor:
    def __init__(self, repo: ComplaintRepository, classifier: ClassifierFn,
                 embedder: Optional[ImageEmbedder] = None, places: Optional[PlaceProvider] = None,
                 settings: Optional[Settings] = None, clock: Callable[[], datetime] = _utc_now):
        self.repo = repo
        self.classifier = classifier
        self.embedder = embedder or NullEmbedder()
        self.places = places or NullPlaceProvider()
        self.settings = settings or Settings.from_env()
        self.clock = clock

    # ====================== POST /complaints/process ======================
    def process_report(self, inp: ReportInput) -> ProcessResult:
        try:
            result = self._process(inp)
            self.repo.commit()
            return result
        except Exception:
            self.repo.rollback()
            raise

    def _process(self, inp: ReportInput) -> ProcessResult:
        s = self.settings
        warnings: List[str] = []

        ai = self._classify(inp, warnings)                                   # 1. AI classification (Module 3)
        gps = validate_gps(inp.latitude, inp.longitude, inp.gps_accuracy, s)  # 2. GPS validation
        warnings += gps.warnings
        now = self.clock()
        embedding = self._embed(inp.image_bytes, warnings)

        decision = self._find_duplicate(ai, inp, embedding, gps.accuracy_m, now)  # 3-4. candidates + CLIP

        dept_name: Optional[str] = None
        if decision.status == DUP_MERGED:                                    # 5. merge or create
            complaint_id = decision.target_complaint_id
            existing = self.repo.get_complaint(complaint_id)
            dept_id = existing.department_id if existing else None
        else:
            complaint_id = uuid.uuid4()
            dept_id, dept_name, warn = resolve_department(ai.issue_type, s, self.repo.get_department_id)  # 7. routing
            if warn:
                warnings.append(warn)
            self.repo.insert_complaint(complaint_id, ai.issue_type, s.new_complaint_status,
                                       inp.latitude, inp.longitude, dept_id, now)

        report_id = self.repo.upsert_report(NewReport(
            complaint_id=complaint_id, latitude=inp.latitude, longitude=inp.longitude, created_at=now,
            report_id=inp.report_id, user_id=inp.user_id, image_url=inp.image_url,
            original_description=ai.original_text or inp.description,
            translated_description=ai.translated_text, gps_accuracy=gps.accuracy_m,
            ai_confidence=ai.confidence, ai_severity=ai.severity, embedding=embedding))
        count = self.repo.refresh_report_count(complaint_id)                 # preserves every individual report

        record = self.repo.get_complaint(complaint_id)                      # 6. priority
        prio = self._priority_for(record, now)
        self.repo.update_complaint_priority(complaint_id, prio.score, prio.band, prio.priority_reason, now)

        return ProcessResult(                                               # 8. saved above
            complaint_id=complaint_id, duplicate_status=decision.status, report_count=count,
            priority_score=prio.score, priority_band=prio.band, priority_reason=prio.priority_reason,
            department_id=dept_id, report_id=report_id, issue_type=ai.issue_type, severity=ai.severity,
            needs_review=ai.needs_review or (decision.status == DUP_POSSIBLE), ai_source=ai.source,
            similarity=decision.similarity, department_name=dept_name,
            possible_duplicate_ids=[p.complaint_id for p in decision.possible], warnings=warnings)

    # ----- helpers -----
    def _classify(self, inp: ReportInput, warnings: List[str]) -> AIResult:
        try:
            ai = normalize_ai(self.classifier(inp.image_bytes, inp.description, inp.language))
        except Exception:  # noqa: BLE001 - Module 3 promises not to raise; guard anyway
            logger.exception("Classifier raised; treating report as unclassified")
            warnings.append("classifier_error")
            ai = AIResult(ISSUE_UNCLASSIFIED, 1, 0.0, "Classifier error", original_text=inp.description,
                          translated_text=inp.description, needs_review=True)
        if ai.issue_type == ISSUE_UNCLASSIFIED:
            ai.needs_review = True
        return ai

    def _embed(self, image_bytes: bytes, warnings: List[str]) -> Optional[List[float]]:
        vec = None
        try:
            vec = self.embedder.embed(image_bytes) if image_bytes else None
        except Exception:  # noqa: BLE001
            logger.exception("Embedder raised")
        if vec is None:
            warnings.append("embedding_unavailable")
        return vec

    def _find_duplicate(self, ai: AIResult, inp: ReportInput, embedding, accuracy, now: datetime) -> DuplicateDecision:
        s = self.settings
        if ai.issue_type == ISSUE_UNCLASSIFIED and not s.merge_unclassified:
            return DuplicateDecision(DUP_NEW)
        candidates = self.repo.find_candidates(
            ai.issue_type, inp.latitude, inp.longitude, s.duplicate_radius_m,
            now - timedelta(days=s.duplicate_window_days), s.eligible_statuses)
        if not candidates:
            return DuplicateDecision(DUP_NEW)
        stored = self.repo.get_embeddings([c.complaint_id for c in candidates])
        scored = [(c, best_similarity(embedding, stored.get(c.complaint_id, []))) for c in candidates]
        return decide_duplicate(scored, s, accuracy)

    def _priority_for(self, record, now: datetime) -> PriorityResult:
        days = max(0, int((now - _aware(record.created_at)).total_seconds() // 86400))
        loc = self.places.context(record.latitude, record.longitude)
        return calculate_priority(record.max_severity or 1, record.report_count, days, loc, record.issue_type)

    # ====================== GET /complaints/{id}/priority ======================
    def get_priority(self, complaint_id: UUID) -> PriorityResponse:
        """Live calculation (days pending keeps growing). Read-only; see refresh_priority() to persist."""
        record = self.repo.get_complaint(complaint_id)
        if record is None:
            raise ComplaintNotFound(str(complaint_id))
        now = self.clock()
        p = self._priority_for(record, now)
        return PriorityResponse(
            complaint_id=complaint_id, priority_score=p.score, priority_band=p.band,
            priority_reason=p.priority_reason, reasons=p.reasons, components=p.components, inputs=p.inputs,
            stored_priority_score=record.priority_score, stored_priority_band=record.priority_band,
            computed_at=now)

    def refresh_priority(self, complaint_id: UUID) -> PriorityResult:
        record = self.repo.get_complaint(complaint_id)
        if record is None:
            raise ComplaintNotFound(str(complaint_id))
        now = self.clock()
        p = self._priority_for(record, now)
        self.repo.update_complaint_priority(complaint_id, p.score, p.band, p.priority_reason, now)
        self.repo.commit()
        return p

    def refresh_open_priorities(self) -> int:
        """Scheduler hook (cron/Celery): stored scores go stale as days_pending grows."""
        ids = self.repo.list_open_complaint_ids(self.settings.eligible_statuses)
        for cid in ids:
            self.refresh_priority(cid)
        return len(ids)

    # ====================== GET /complaints/{id}/duplicates ======================
    def get_duplicates(self, complaint_id: UUID) -> DuplicatesResponse:
        record = self.repo.get_complaint(complaint_id)
        if record is None:
            raise ComplaintNotFound(str(complaint_id))
        s = self.settings
        reports = self.repo.get_reports(complaint_id)
        own = self.repo.get_embeddings([complaint_id]).get(complaint_id, [])
        now = self.clock()
        cands = self.repo.find_candidates(record.issue_type, record.latitude, record.longitude,
                                          s.duplicate_radius_m, now - timedelta(days=s.duplicate_window_days),
                                          s.eligible_statuses, exclude_complaint_id=complaint_id)
        stored = self.repo.get_embeddings([c.complaint_id for c in cands]) if cands else {}
        possible: List[PossibleDuplicateOut] = []
        for c in cands:
            sims = [best_similarity(e, stored.get(c.complaint_id, [])) for e in own] or [None]
            sims = [x for x in sims if x is not None]
            sim = max(sims) if sims else None
            if sim is None:
                possible.append(PossibleDuplicateOut(complaint_id=c.complaint_id, similarity=None,
                                                     reason="image similarity unavailable"))
            elif sim >= s.possible_similarity_threshold:
                possible.append(PossibleDuplicateOut(complaint_id=c.complaint_id, similarity=round(sim, 4),
                                                     reason="image similarity above review threshold"))
        possible.sort(key=lambda p: (p.similarity is None, -(p.similarity or 0)))
        return DuplicatesResponse(
            complaint_id=complaint_id, report_count=record.report_count,
            reports=[MergedReportOut(report_id=r.id, created_at=r.created_at, image_url=r.image_url,
                                     latitude=r.latitude, longitude=r.longitude) for r in reports],
            possible_duplicates=possible)

    # ====================== POST /complaints/{id}/split ======================
    def split_complaint(self, complaint_id: UUID, report_ids: Sequence[UUID], officer_id: Optional[UUID],
                        comment: Optional[str] = None) -> SplitResponse:
        """Move the given reports onto a brand-new complaint (reverses an incorrect merge)."""
        try:
            resp = self._split(complaint_id, list(dict.fromkeys(report_ids)), officer_id, comment)
            self.repo.commit()
            return resp
        except Exception:
            self.repo.rollback()
            raise

    def _split(self, complaint_id, report_ids, officer_id, comment) -> SplitResponse:
        record = self.repo.get_complaint(complaint_id)
        if record is None:
            raise ComplaintNotFound(str(complaint_id))
        if not report_ids:
            raise SplitError("No report ids supplied")
        reports = {r.id: r for r in self.repo.get_reports(complaint_id)}
        unknown = [str(r) for r in report_ids if r not in reports]
        if unknown:
            raise SplitError(f"Reports not part of this complaint: {', '.join(unknown)}")
        if len(report_ids) >= len(reports):
            raise SplitError("Cannot move every report; the original complaint must keep at least one")

        now = self.clock()
        moved = [reports[r] for r in report_ids]
        anchor = min(moved, key=lambda r: r.created_at)  # earliest moved report defines the new complaint
        lat = anchor.latitude if anchor.latitude is not None else record.latitude
        lon = anchor.longitude if anchor.longitude is not None else record.longitude
        new_id = uuid.uuid4()
        # Same category as the original (reports carry no issue_type); an officer can reclassify afterwards.
        self.repo.insert_complaint(new_id, record.issue_type, record.status, lat, lon,
                                   record.department_id, anchor.created_at)
        self.repo.move_reports(report_ids, new_id)
        orig_count = self.repo.refresh_report_count(complaint_id)
        new_count = self.repo.refresh_report_count(new_id)

        orig_p = self._priority_for(self.repo.get_complaint(complaint_id), now)
        new_p = self._priority_for(self.repo.get_complaint(new_id), now)
        self.repo.update_complaint_priority(complaint_id, orig_p.score, orig_p.band, orig_p.priority_reason, now)
        self.repo.update_complaint_priority(new_id, new_p.score, new_p.band, new_p.priority_reason, now)

        note = f"Split: {len(report_ids)} report(s) moved to complaint {new_id}"
        self.repo.add_status_history(complaint_id, officer_id, record.status, record.status,
                                     f"{note}. {comment}" if comment else note, now)
        self.repo.add_status_history(new_id, officer_id, record.status, record.status,
                                     f"Created by splitting complaint {complaint_id}", now)
        return SplitResponse(
            original_complaint_id=complaint_id, new_complaint_id=new_id, moved_report_ids=list(report_ids),
            original_report_count=orig_count, new_report_count=new_count,
            original_priority_score=orig_p.score, original_priority_band=orig_p.band,
            new_priority_score=new_p.score, new_priority_band=new_p.band)
