"""Adapter between the officer dashboard and Module 4's duplicate service.

Module 5 contains NO duplicate-detection logic. It calls the functions below on
the Module 4 service module (``M4_DUPLICATE_SERVICE_MODULE``). If Module 4 names
them differently, adapt the four wrappers here - nothing else changes.

Expected Module 4 functions (all receive the SQLAlchemy session first):
    list_duplicate_candidates(db, *, status, limit, offset) -> {"items": [...], "total": int}
    candidates_for_complaint(db, complaint_id) -> [candidate dict, ...]
    confirm_merge(db, candidate_id, officer_id) -> dict
    reject_merge(db, candidate_id, officer_id) -> dict
    split_complaint(db, complaint_id, report_ids, officer_id, reason) -> dict

A candidate dict is expected to contain: id, complaint_id, candidate_complaint_id,
similarity (0-1), distance_m, reason, created_at. Extra keys are passed through.
"""
import importlib
import logging

from .config import get_settings
from .errors import ServiceError

log = logging.getLogger(__name__)


class DuplicateServiceUnavailable(ServiceError):
    status_code = 501


def _service():
    name = get_settings().duplicate_service_module
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise DuplicateServiceUnavailable(
            "duplicate_service_unavailable",
            f"Module 4's duplicate service ('{name}') is not installed in this deployment.",
        ) from exc


def _call(name: str):
    fn = getattr(_service(), name, None)
    if fn is None:
        raise DuplicateServiceUnavailable(
            "duplicate_service_incomplete", f"Module 4's duplicate service has no '{name}' function."
        )
    return fn


def list_candidates(db, *, status: str, limit: int, offset: int) -> dict:
    return _call("list_duplicate_candidates")(db, status=status, limit=limit, offset=offset)


def candidates_for(db, complaint_id) -> list:
    """Best-effort: the detail page must still load if Module 4 is unavailable."""
    try:
        return list(_call("candidates_for_complaint")(db, complaint_id))
    except ServiceError:
        return []
    except Exception:  # noqa: BLE001 - never let a duplicate lookup break the detail page
        log.exception("candidates_for_complaint failed")
        return []


def confirm_merge(db, candidate_id, officer_id) -> dict:
    return _call("confirm_merge")(db, candidate_id, officer_id)


def reject_merge(db, candidate_id, officer_id) -> dict:
    return _call("reject_merge")(db, candidate_id, officer_id)


def split_complaint(db, complaint_id, report_ids, officer_id, reason) -> dict:
    return _call("split_complaint")(db, complaint_id, report_ids, officer_id, reason)


def maybe_reroute(db, complaint_id) -> None:
    """Optional: ask Module 4 to re-run department routing after an AI correction.
    Set M4_REROUTE_HOOK='package.module:function'. Failures are logged, never raised."""
    target = get_settings().reroute_hook
    if not target:
        return
    module_name, _, attr = target.partition(":")
    try:
        getattr(importlib.import_module(module_name), attr)(db, complaint_id)
    except Exception:  # noqa: BLE001
        log.exception("reroute hook failed for complaint %s", complaint_id)
