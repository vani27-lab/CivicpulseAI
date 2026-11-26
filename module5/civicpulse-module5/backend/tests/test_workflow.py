import pytest

from app.officer.errors import TransitionError, ValidationFailed
from app.officer.workflow import Status, allowed_next, normalize_status, to_db_value, validate_transition


def ok(current, new, **kw):
    base = dict(role_is_admin=False, comment=None, has_after_photo=False)
    base.update(kw)
    return validate_transition(current, new, **base)


def test_normalize_accepts_every_spelling():
    for raw in ("In Progress", "in-progress", "IN_PROGRESS", " in_progress "):
        assert normalize_status(raw) is Status.IN_PROGRESS
    assert normalize_status("garbage") is None
    assert normalize_status(None) is None


def test_to_db_value_respects_style():
    assert to_db_value(Status.IN_PROGRESS, "snake") == "in_progress"
    assert to_db_value(Status.IN_PROGRESS, "title") == "In Progress"


def test_happy_path_forward():
    assert ok(Status.SUBMITTED, Status.ASSIGNED) is False
    assert ok(Status.ASSIGNED, Status.IN_PROGRESS) is False
    assert ok(Status.IN_PROGRESS, Status.RESOLVED, has_after_photo=True) is False


def test_cannot_skip_steps():
    with pytest.raises(TransitionError) as exc:
        ok(Status.SUBMITTED, Status.RESOLVED, has_after_photo=True)
    assert exc.value.code == "invalid_transition"


def test_same_status_rejected():
    with pytest.raises(TransitionError) as exc:
        ok(Status.ASSIGNED, Status.ASSIGNED)
    assert exc.value.code == "same_status"


def test_resolution_requires_after_photo():
    with pytest.raises(ValidationFailed) as exc:
        ok(Status.IN_PROGRESS, Status.RESOLVED)
    assert exc.value.code == "after_photo_required"


def test_rejection_requires_comment():
    with pytest.raises(ValidationFailed) as exc:
        ok(Status.SUBMITTED, Status.REJECTED, comment="   ")
    assert exc.value.code == "comment_required"
    assert ok(Status.SUBMITTED, Status.REJECTED, comment="Not a civic issue") is False


def test_rejected_can_be_disabled():
    with pytest.raises(ValidationFailed):
        ok(Status.SUBMITTED, Status.REJECTED, comment="x", rejected_enabled=False)
    assert Status.REJECTED not in allowed_next(Status.SUBMITTED, False, rejected_enabled=False)


def test_officer_cannot_reopen_but_admin_can():
    assert allowed_next(Status.RESOLVED, False) == []
    assert Status.IN_PROGRESS in allowed_next(Status.RESOLVED, True)
    with pytest.raises(TransitionError):
        ok(Status.RESOLVED, Status.IN_PROGRESS)
    assert ok(Status.RESOLVED, Status.IN_PROGRESS, role_is_admin=True) is False


def test_override_is_admin_only():
    with pytest.raises(TransitionError) as exc:
        ok(Status.IN_PROGRESS, Status.RESOLVED, admin_override=True, override_reason="urgent fix confirmed")
    assert exc.value.code == "override_forbidden"
    assert exc.value.status_code == 403


def test_override_needs_reason_and_skips_photo_rule():
    with pytest.raises(ValidationFailed) as exc:
        ok(Status.IN_PROGRESS, Status.RESOLVED, role_is_admin=True, admin_override=True, override_reason=" ")
    assert exc.value.code == "override_reason_required"
    used = ok(
        Status.IN_PROGRESS, Status.RESOLVED, role_is_admin=True, admin_override=True,
        override_reason="Photo lost; verified on site",
    )
    assert used is True


def test_unknown_current_status():
    with pytest.raises(TransitionError):
        ok(None, Status.ASSIGNED)
