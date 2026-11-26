import uuid
from datetime import datetime, timezone

import pytest

from app.modules.complaint_engine.config import Settings
from app.modules.complaint_engine.domain import Candidate
from app.modules.complaint_engine.duplicates import best_similarity, cosine_similarity, decide_duplicate

S = Settings()


def cand():
    return Candidate(uuid.uuid4(), "pothole", "submitted", 1, datetime(2026, 1, 1, tzinfo=timezone.utc), 0, 0)


def test_cosine_basics():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([1, 0], [1, 0, 0]) is None
    assert cosine_similarity([0, 0], [1, 0]) is None
    assert cosine_similarity(None, [1, 0]) is None


def test_best_similarity_takes_max_over_reports():
    assert best_similarity([1, 0], [[0, 1], [1, 0]]) == pytest.approx(1.0)
    assert best_similarity([1, 0], []) is None


def test_no_candidates_is_new():
    assert decide_duplicate([], S, None).status == "new"


def test_high_similarity_merges_best_candidate():
    a, b = cand(), cand()
    d = decide_duplicate([(a, 0.93), (b, 0.97)], S, 10)
    assert d.status == "merged" and d.target_complaint_id == b.complaint_id


def test_moderate_similarity_is_possible_not_merged():
    a = cand()
    d = decide_duplicate([(a, 0.88)], S, 10)
    assert d.status == "possible_duplicate" and d.target_complaint_id is None
    assert d.possible[0].complaint_id == a.complaint_id


def test_low_similarity_is_new():
    assert decide_duplicate([(cand(), 0.4)], S, 10).status == "new"


def test_distance_alone_never_confirms():
    d = decide_duplicate([(cand(), None)], S, 5)
    assert d.status == "possible_duplicate" and d.target_complaint_id is None


def test_low_gps_accuracy_blocks_auto_merge():
    a = cand()
    d = decide_duplicate([(a, 0.99)], S, 80)
    assert d.status == "possible_duplicate" and d.possible[0].complaint_id == a.complaint_id


def test_threshold_is_configurable():
    strict = Settings(merge_similarity_threshold=0.99)
    assert decide_duplicate([(cand(), 0.95)], strict, None).status == "possible_duplicate"
