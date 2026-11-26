from app.modules.citizen_tracking.shaping import public_history, compute_stats, norm
from app.modules.citizen_tracking.translation import translate_cached
from datetime import datetime

def row(new, photo="a.jpg", comment=None):
    return {"id": "1", "old_status": None, "new_status": new, "comment": comment,
            "after_photo_url": photo, "created_at": datetime(2026, 1, 1), "officer_id": "secret"}

def test_norm(): assert norm("In Progress") == "in_progress"
def test_history_hides_officer_and_early_photos():
    h = public_history([row("Assigned"), row("Resolved")])
    assert h[0]["after_photo_url"] is None and h[1]["after_photo_url"] == "a.jpg"
    assert all("officer_id" not in x for x in h)
def test_stats():
    assert compute_stats(["submitted", "assigned", "in_progress", "resolved", "rejected"]) == \
        {"total": 5, "pending": 2, "in_progress": 1, "resolved": 1}

class FakeDB:
    def execute(self, *a, **k): raise RuntimeError("db down")
    def rollback(self): pass
def test_translation_failure_returns_none():
    assert translate_cached(FakeDB(), "1", "hello", "hi") is None
def test_english_skips_translation():
    assert translate_cached(FakeDB(), "1", "hello", "en") is None
