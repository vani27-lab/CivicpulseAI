import uuid

import pytest

from app.modules.complaint_engine.config import Settings
from app.modules.complaint_engine.exceptions import InvalidGPSError
from app.modules.complaint_engine.gps import validate_gps
from app.modules.complaint_engine.places import NullPlaceProvider, StaticPlaceProvider, haversine_m
from app.modules.complaint_engine.routing import department_name_for, resolve_department

S = Settings()


@pytest.mark.parametrize("lat,lon", [
    (None, 77), (27, None), (float("nan"), 77), (91, 77), (27, 181), (0, 0), (51.5, -0.12), ("27", "77"), (True, 77),
])
def test_invalid_gps_rejected(lat, lon):
    with pytest.raises(InvalidGPSError):
        validate_gps(lat, lon, 10, S)


def test_valid_gps_and_accuracy_warnings():
    assert validate_gps(27.49, 77.67, 10, S).warnings == []
    assert "low_gps_accuracy" in validate_gps(27.49, 77.67, 500, S).warnings
    assert "gps_accuracy_unknown" in validate_gps(27.49, 77.67, None, S).warnings
    assert "gps_accuracy_invalid" in validate_gps(27.49, 77.67, -5, S).warnings


def test_bbox_can_be_disabled():
    assert validate_gps(51.5, -0.12, 10, Settings(gps_bbox_enabled=False)).warnings == []


def test_haversine_roughly_111m_per_milli_degree():
    assert haversine_m(27.0, 77.0, 27.001, 77.0) == pytest.approx(111.2, abs=1.0)


def _places(*items):
    return StaticPlaceProvider([dict(kind=k, lat=27.0 + dlat, lon=77.0, name=k) for k, dlat in items], S)


def test_school_within_200m_is_factor_1():
    c = _places(("school", 0.0013)).context(27.0, 77.0)   # ~145 m
    assert (c.factor, c.kind) == (1.0, "school")


def test_hospital_beyond_200m_is_ignored():
    assert _places(("hospital", 0.0025)).context(27.0, 77.0).factor == 0.0  # ~278 m


def test_market_is_half_and_school_wins_over_market():
    assert _places(("market", 0.0007)).context(27.0, 77.0).factor == 0.5
    assert _places(("market", 0.0003), ("school", 0.0010)).context(27.0, 77.0).factor == 1.0


def test_invalid_entries_ignored_and_null_provider():
    p = StaticPlaceProvider([{"kind": "zoo", "lat": 1, "lon": 1}, "junk", {"kind": "school"}], S)
    assert p.context(1, 1).factor == 0.0
    assert NullPlaceProvider().context(1, 1).factor == 0.0


def test_routing_table():
    for issue, dept in [("pothole", "Roads"), ("road_damage", "Roads"), ("garbage", "Sanitation"),
                        ("broken_streetlight", "Electrical"), ("blocked_drain", "Drainage"),
                        ("unclassified", "Manual review"), ("other", "Manual review"), ("weird", "Manual review")]:
        assert department_name_for(issue, S) == dept


def test_resolve_department_found_and_missing():
    did = uuid.uuid4()
    assert resolve_department("pothole", S, lambda n: did if n == "Roads" else None) == (did, "Roads", None)
    d, name, warn = resolve_department("garbage", S, lambda n: None)
    assert d is None and warn == "department_not_found:Sanitation"
