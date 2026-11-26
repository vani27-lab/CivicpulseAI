import uuid
from datetime import timedelta

import pytest

from app.modules.complaint_engine.config import Settings
from app.modules.complaint_engine.domain import LocationContext
from app.modules.complaint_engine.exceptions import ComplaintNotFound, InvalidGPSError, SplitError
from tests.helpers import DEPTS, LAT, LON, FakeClassifier, FakeEmbedder, ai, make, report, vec

A = [1.0, 0.0]
EMB = {b"img-a": A, b"img-same": vec(0.95), b"img-maybe": vec(0.88), b"img-other": [0.0, 1.0]}
M30 = 0.00027   # ~30 m in latitude degrees
M80 = 0.00072   # ~80 m


def proc(**kw):
    return make(embedder=FakeEmbedder(EMB), **kw)


def test_first_report_creates_complaint_routes_and_scores():
    p, repo, _ = proc()
    r = p.process_report(report())
    assert (r.duplicate_status, r.report_count, r.department_id) == ("new", 1, DEPTS["Roads"])
    assert r.priority_band in ("HIGH", "MEDIUM", "LOW") and r.priority_reason.startswith(r.priority_band)
    assert repo.complaints[r.complaint_id]["status"] == "submitted" and repo.commits == 1


def test_similar_nearby_report_merges_and_preserves_both_reports():
    p, repo, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    r2 = p.process_report(report(b"img-same", lat=LAT + M30))
    assert r2.duplicate_status == "merged" and r2.complaint_id == r1.complaint_id
    assert r2.report_count == 2 and len(repo.reports) == 2
    assert r2.priority_score > r1.priority_score          # more reports => recalculated higher
    assert "2 citizen reports." in r2.priority_reason


def test_nearby_but_different_image_creates_new_complaint():
    p, repo, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    r2 = p.process_report(report(b"img-other", lat=LAT + M30))
    assert r2.duplicate_status == "new" and r2.complaint_id != r1.complaint_id


def test_uncertain_similarity_is_flagged_possible_and_not_merged():
    p, repo, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    r2 = p.process_report(report(b"img-maybe", lat=LAT + M30))
    assert r2.duplicate_status == "possible_duplicate" and r2.complaint_id != r1.complaint_id
    assert r1.complaint_id in r2.possible_duplicate_ids and r2.needs_review is True


def test_identical_image_beyond_50m_is_not_a_candidate():
    p, _, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    r2 = p.process_report(report(b"img-a", lat=LAT + M80))
    assert r2.duplicate_status == "new" and r2.complaint_id != r1.complaint_id


def test_different_issue_type_never_merges():
    p, _, _ = make(embedder=FakeEmbedder(EMB))
    p.process_report(report(b"img-a"))
    p.classifier = FakeClassifier(ai("garbage"))
    r = p.process_report(report(b"img-a", lat=LAT + M30))
    assert r.duplicate_status == "new" and r.department_id == DEPTS["Sanitation"]


def test_complaint_older_than_30_days_is_not_a_candidate():
    p, _, clock = proc()
    p.process_report(report(b"img-a"))
    clock.advance(days=31)
    assert p.process_report(report(b"img-same")).duplicate_status == "new"


def test_ineligible_status_is_not_a_candidate():
    p, repo, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    repo.complaints[r1.complaint_id]["status"] = "resolved"
    assert p.process_report(report(b"img-same")).duplicate_status == "new"


def test_no_embedder_never_auto_merges():
    p, _, _ = make()  # NullEmbedder-like fake returns None
    p.process_report(report(b"img-a"))
    r = p.process_report(report(b"img-a"))
    assert r.duplicate_status == "possible_duplicate" and "embedding_unavailable" in r.warnings


def test_poor_gps_accuracy_blocks_auto_merge():
    p, _, _ = proc()
    p.process_report(report(b"img-a"))
    r = p.process_report(report(b"img-same", gps_accuracy=90))
    assert r.duplicate_status == "possible_duplicate"


def test_unclassified_is_never_merged_and_goes_to_manual_review():
    p, _, _ = proc(classifier=FakeClassifier(ai("unclassified", 1, 0.0)))
    p.process_report(report(b"img-a"))
    r = p.process_report(report(b"img-a"))
    assert r.duplicate_status == "new" and r.needs_review is True
    assert r.department_id == DEPTS["Manual review"]


def test_invalid_gps_raises_and_creates_nothing():
    p, repo, _ = proc()
    with pytest.raises(InvalidGPSError):
        p.process_report(report(lat=0.0, lon=0.0))
    assert repo.complaints == {} and repo.rollbacks == 1


def test_classifier_exception_degrades_to_unclassified():
    p, repo, _ = proc(classifier=FakeClassifier(error=RuntimeError("boom")))
    r = p.process_report(report())
    assert r.issue_type == "unclassified" and "classifier_error" in r.warnings and len(repo.complaints) == 1


def test_missing_department_is_warned_not_fatal():
    p, _, _ = proc(departments={})
    r = p.process_report(report())
    assert r.department_id is None and any(w.startswith("department_not_found") for w in r.warnings)


def test_highest_severity_across_reports_drives_priority():
    p, _, _ = proc(classifier=FakeClassifier(ai(severity=1)))
    p.process_report(report(b"img-a"))
    p.classifier = FakeClassifier(ai(severity=4))
    r = p.process_report(report(b"img-same"))
    assert r.duplicate_status == "merged" and r.priority_band == "HIGH"


def test_existing_report_row_from_module2_is_reused():
    p, repo, _ = proc()
    rid = uuid.uuid4()
    r = p.process_report(report(report_id=rid))
    assert r.report_id == rid and rid in repo.reports


def test_location_factor_feeds_priority():
    class School:
        def context(self, lat, lon):
            return LocationContext(1.0, "school")
    p, _, _ = proc(places=School())
    r = p.process_report(report())
    assert "School nearby." in r.priority_reason


def test_live_priority_grows_with_days_pending():
    p, _, clock = proc()
    r = p.process_report(report())
    clock.advance(days=9)
    live = p.get_priority(r.complaint_id)
    assert live.inputs["days_pending"] == 9 and live.priority_score > r.priority_score
    assert live.stored_priority_score == r.priority_score
    assert "Pending for 9 days." in live.reasons


def test_refresh_open_priorities_persists():
    p, repo, clock = proc()
    r = p.process_report(report())
    clock.advance(days=14)
    assert p.refresh_open_priorities() == 1
    assert repo.complaints[r.complaint_id]["priority_score"] > r.priority_score


def test_unknown_complaint_raises():
    p, _, _ = proc()
    with pytest.raises(ComplaintNotFound):
        p.get_priority(uuid.uuid4())
    with pytest.raises(ComplaintNotFound):
        p.get_duplicates(uuid.uuid4())


def test_duplicates_endpoint_lists_reports_and_possibles():
    p, _, _ = proc()
    r1 = p.process_report(report(b"img-a"))
    r2 = p.process_report(report(b"img-maybe", lat=LAT - M30))         # possible dup, own complaint
    d1 = p.get_duplicates(r1.complaint_id)
    assert len(d1.reports) == 1 and d1.report_count == 1
    assert [x.complaint_id for x in d1.possible_duplicates] == [r2.complaint_id]
    p.process_report(report(b"img-same", lat=LAT + M30))               # merges into r1
    assert len(p.get_duplicates(r1.complaint_id).reports) == 2


def _merged_three():
    p, repo, clock = proc()
    r1 = p.process_report(report(b"img-a"))
    clock.advance(days=2)
    p.process_report(report(b"img-same", lat=LAT + M30))
    r3 = p.process_report(report(b"img-same", lat=LAT - M30))
    assert r3.report_count == 3
    return p, repo, clock, r1.complaint_id


def test_split_moves_report_to_new_complaint_and_recalculates_both():
    p, repo, clock, cid = _merged_three()
    reports = repo.get_reports(cid)
    officer = uuid.uuid4()
    before = repo.complaints[cid]["priority_score"]
    out = p.split_complaint(cid, [reports[2].id], officer, "wrong merge")
    assert (out.original_report_count, out.new_report_count) == (2, 1)
    assert out.new_complaint_id != cid and repo.reports[reports[2].id]["complaint_id"] == out.new_complaint_id
    assert out.original_priority_score < before
    assert len(repo.get_reports(cid)) + len(repo.get_reports(out.new_complaint_id)) == 3   # nothing lost
    assert {h["officer_id"] for h in repo.history} == {officer} and len(repo.history) == 2
    assert repo.complaints[out.new_complaint_id]["department_id"] == DEPTS["Roads"]


def test_split_validation():
    p, repo, _, cid = _merged_three()
    ids = [r.id for r in repo.get_reports(cid)]
    with pytest.raises(SplitError):
        p.split_complaint(cid, ids, None)                       # would empty the original
    with pytest.raises(SplitError):
        p.split_complaint(cid, [uuid.uuid4()], None)            # not part of complaint
    with pytest.raises(SplitError):
        p.split_complaint(cid, [], None)
    with pytest.raises(ComplaintNotFound):
        p.split_complaint(uuid.uuid4(), ids[:1], None)
    assert len(repo.get_reports(cid)) == 3                      # failed splits changed nothing
