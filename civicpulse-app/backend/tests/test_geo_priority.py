"""Unit tests for the Geo-Aware Intelligent Priority Engine.

Tests:
- Haversine proximity calculation
- Facility category classification & impact multipliers
- Priority engine 5-factor formula and bands (LOW, MEDIUM, HIGH, CRITICAL)
- Emergency escalation rules for life-safety threats near hospitals/fire stations
- Transparent fallback behavior when external map service is unavailable
"""
import pytest
from app.services.geo_facility_service import (
    haversine_distance_m,
    get_facility_impact_multiplier,
    analyze_geospatial_impact,
    CAT_HOSPITAL,
    CAT_SCHOOL,
    CAT_FIRE_STATION,
)
from app.modules.complaint_engine.priority import calculate_priority, band_for
from app.modules.complaint_engine.domain import LocationContext
from app.modules.complaint_engine.constants import (
    BAND_LOW,
    BAND_MEDIUM,
    BAND_HIGH,
    BAND_CRITICAL,
)


def test_haversine_distance_calculation():
    # Distance between Mathura District Hospital (27.4932, 77.6740)
    # and a nearby complaint at (27.4925, 77.6735)
    dist = haversine_distance_m(27.4932, 77.6740, 27.4925, 77.6735)
    assert 80.0 <= dist <= 110.0  # Approx 92m
    # Same point should be 0.0
    assert haversine_distance_m(27.5, 77.5, 27.5, 77.5) == 0.0


def test_facility_impact_multipliers():
    # Dangerous road blockage near a hospital gets top multiplier (2.0)
    hosp_pothole_mult = get_facility_impact_multiplier("pothole", CAT_HOSPITAL)
    assert hosp_pothole_mult == 2.0

    # Pothole near fire station gets 1.9 (engine dispatch obstruction)
    fire_pothole_mult = get_facility_impact_multiplier("pothole", CAT_FIRE_STATION)
    assert fire_pothole_mult == 1.9

    # Streetlight near school gets 1.4 (child safety in evening/morning)
    school_light_mult = get_facility_impact_multiplier("streetlight", CAT_SCHOOL)
    assert school_light_mult == 1.4

    # Minor streetlight issue far away / standard gets lower multiplier
    assert get_facility_impact_multiplier("streetlight", "market") <= 1.2


def test_priority_bands_and_thresholds():
    # 0-29: LOW
    assert band_for(15.0, severity=1) == BAND_LOW
    assert band_for(29.0, severity=1) == BAND_LOW

    # 30-49: MEDIUM
    assert band_for(30.0, severity=2) == BAND_MEDIUM
    assert band_for(45.0, severity=2) == BAND_MEDIUM

    # 50-74: HIGH
    assert band_for(50.0, severity=3) == BAND_HIGH
    assert band_for(72.0, severity=3) == BAND_HIGH

    # 75-100: CRITICAL
    assert band_for(75.0, severity=3) == BAND_CRITICAL
    assert band_for(90.0, severity=4) == BAND_CRITICAL

    # Emergency forced escalation
    assert band_for(40.0, severity=2, is_emergency=True) == BAND_CRITICAL


def test_emergency_escalation_near_hospital():
    # A serious pothole (severity 3) directly outside a hospital entrance (29m)
    loc = LocationContext(
        factor=1.0,
        kind=CAT_HOSPITAL,
        name="City Civil Hospital Trauma Centre",
        distance_m=29.0,
        is_emergency=True,
    )
    result = calculate_priority(
        severity=3,
        reports=2,
        days_pending=1,
        location=loc,
        issue_type="pothole",
    )
    assert result.band == BAND_CRITICAL
    assert result.score >= 75.0
    assert any("EMERGENCY ESCALATION" in r for r in result.reasons)
    assert any("Civil Hospital" in r for r in result.reasons)


def test_low_priority_isolated_complaint():
    # Minor issue (severity 1), single report, zero pending days, no nearby facilities
    loc = LocationContext(factor=0.0, kind=None, distance_m=None)
    result = calculate_priority(
        severity=1,
        reports=1,
        days_pending=0,
        location=loc,
        issue_type="garbage",
    )
    assert result.band == BAND_LOW
    assert result.score < 30.0
    assert result.is_emergency is False


def test_geospatial_impact_offline_fallback():
    # When coordinates are provided, analyze_geospatial_impact identifies
    # the nearest facility using the seed/cache without failing even if offline
    res = analyze_geospatial_impact(
        lat=27.4932,
        lon=27.6740,
        issue_type="pothole",
        severity=3,
        db=None,  # No db required
    )
    assert res is not None
    assert res.location_factor >= 0.0
    assert len(res.reasons) > 0
    assert res.public_impact_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
