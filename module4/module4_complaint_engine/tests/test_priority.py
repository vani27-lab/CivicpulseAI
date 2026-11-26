import math

import pytest

from app.modules.complaint_engine.domain import LocationContext
from app.modules.complaint_engine.priority import band_for, calculate_priority

NONE = LocationContext()
SCHOOL = LocationContext(1.0, "school")


def test_exact_formula_minimum_case():
    # severity 4, 1 report, 0 days, no location: 100 * (0.40 + 0.25 * ln2/ln21)
    p = calculate_priority(4, 1, 0, NONE, "pothole")
    assert p.score == pytest.approx(100 * (0.40 + 0.25 * math.log(2) / math.log(21)), abs=0.01)
    assert p.score == pytest.approx(45.69, abs=0.01)


def test_maximum_is_100():
    assert calculate_priority(4, 50, 100, SCHOOL).score == 100.0


def test_report_term_caps_at_20_reports():
    a = calculate_priority(2, 20, 0, NONE).score
    b = calculate_priority(2, 500, 0, NONE).score
    assert a == b


def test_age_term_caps_at_14_days():
    assert calculate_priority(2, 1, 14, NONE).score == calculate_priority(2, 1, 90, NONE).score


@pytest.mark.parametrize("score,sev,band", [
    (59.99, 3, "MEDIUM"), (60.0, 1, "HIGH"), (40.0, 1, "MEDIUM"),
    (39.99, 1, "LOW"), (39.99, 4, "HIGH"), (0, 4, "HIGH"),
])
def test_band_boundaries(score, sev, band):
    assert band_for(score, sev) == band


def test_severity_4_forces_high_even_with_low_score():
    p = calculate_priority(4, 1, 0, NONE)
    assert p.score < 60 and p.band == "HIGH"
    assert "Critical severity forces HIGH priority." in p.reasons


def test_reasons_come_from_actual_factors():
    p = calculate_priority(3, 5, 9, SCHOOL, "road_damage")
    assert p.reasons[0] == "Serious road damage."
    assert "5 citizen reports." in p.reasons
    assert "Pending for 9 days." in p.reasons
    assert "School nearby." in p.reasons
    assert p.priority_reason.startswith(f"{p.band} — ")


def test_no_reason_for_absent_factors():
    p = calculate_priority(2, 1, 0, NONE, "garbage")
    assert p.reasons == ["Moderate garbage accumulation."]


def test_inputs_clamped():
    p = calculate_priority(9, 0, -3, NONE)
    assert p.inputs["severity"] == 4 and p.inputs["reports"] == 1 and p.inputs["days_pending"] == 0
