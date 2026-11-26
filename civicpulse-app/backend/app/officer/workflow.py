"""Complaint status workflow. Pure logic, no I/O.

The server is the single authority on which transitions are legal. The detail
endpoint returns ``allowed_next_statuses`` so the frontend never hardcodes rules.
"""
from enum import Enum

from .errors import TransitionError, ValidationFailed


class Status(str, Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


STATUS_LABELS = {
    Status.SUBMITTED: "Submitted",
    Status.ASSIGNED: "Assigned",
    Status.IN_PROGRESS: "In Progress",
    Status.RESOLVED: "Resolved",
    Status.REJECTED: "Rejected",
}

# Forward workflow available to every officer.
OFFICER_TRANSITIONS = {
    Status.SUBMITTED: [Status.ASSIGNED, Status.IN_PROGRESS, Status.REJECTED],
    Status.ASSIGNED: [Status.IN_PROGRESS, Status.REJECTED],
    Status.IN_PROGRESS: [Status.RESOLVED, Status.ASSIGNED, Status.REJECTED],
    Status.RESOLVED: [],
    Status.REJECTED: [],
}

# Extra transitions only admins get (reopening closed complaints).
ADMIN_EXTRA_TRANSITIONS = {
    Status.RESOLVED: [Status.IN_PROGRESS],
    Status.REJECTED: [Status.SUBMITTED],
}

MIN_OVERRIDE_REASON = 5


def normalize_status(raw) -> Status | None:
    """Map any stored spelling ('In Progress', 'in-progress', 'IN_PROGRESS') to a Status."""
    if raw is None:
        return None
    key = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    try:
        return Status(key)
    except ValueError:
        return None


def to_db_value(status: Status, style: str = "snake") -> str:
    """Spell a status the way the existing database stores it."""
    if style == "title":
        return STATUS_LABELS[status]
    return status.value


def allowed_next(current: Status, role_is_admin: bool, rejected_enabled: bool = True) -> list[Status]:
    options = list(OFFICER_TRANSITIONS.get(current, []))
    if role_is_admin:
        options += ADMIN_EXTRA_TRANSITIONS.get(current, [])
    if not rejected_enabled:
        options = [s for s in options if s is not Status.REJECTED]
    return options


def validate_transition(
    current: Status | None,
    new: Status,
    *,
    role_is_admin: bool,
    comment: str | None,
    has_after_photo: bool,
    admin_override: bool = False,
    override_reason: str | None = None,
    rejected_enabled: bool = True,
) -> bool:
    """Raise TransitionError/ValidationFailed if the update is not allowed.

    Returns True when an admin override was exercised (so the caller can mark the
    history entry), False for an ordinary transition.
    """
    if current is None:
        raise TransitionError("unknown_current_status", "The complaint has a status the workflow does not recognise.")
    if new is current:
        raise TransitionError("same_status", "The complaint is already in that status.")
    if new is Status.REJECTED and not rejected_enabled:
        raise ValidationFailed("rejected_disabled", "Rejecting complaints is not enabled for this deployment.")

    if admin_override:
        if not role_is_admin:
            raise TransitionError("override_forbidden", "Only an admin can override the workflow.", 403)
        if not override_reason or len(override_reason.strip()) < MIN_OVERRIDE_REASON:
            raise ValidationFailed("override_reason_required", "An admin override needs a written reason.")
        return True

    if new not in allowed_next(current, role_is_admin, rejected_enabled):
        raise TransitionError(
            "invalid_transition",
            f"A complaint cannot move from {STATUS_LABELS[current]} to {STATUS_LABELS[new]}.",
        )
    if new is Status.RESOLVED and not has_after_photo:
        raise ValidationFailed("after_photo_required", "Upload an after-photo to resolve this complaint.")
    if new is Status.REJECTED and not (comment and comment.strip()):
        raise ValidationFailed("comment_required", "Explain why the complaint is being rejected.")
    return False
