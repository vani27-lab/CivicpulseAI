from datetime import date

import pytest

from app.officer.errors import ValidationFailed
from app.officer.queries import ComplaintFilters, build_list_sql, build_map_sql, build_order_by, like_pattern


def test_default_sort_puts_high_first():
    order = build_order_by("priority", "desc")
    assert "WHEN 'HIGH' THEN 0" in order
    assert order.index("ASC") < order.index("priority_score")  # band rank ascending => HIGH first
    assert "priority_score DESC" in order


def test_priority_asc_reverses():
    order = build_order_by("priority", "asc")
    assert "priority_score ASC" in order


def test_sort_whitelist_blocks_injection():
    with pytest.raises(ValidationFailed):
        build_order_by("created_at; DROP TABLE complaints", "desc")


def test_filters_use_bind_parameters_only():
    f = ComplaintFilters(q="road'; DROP", department_id="d1", issue_type="Pothole", priority_band="high",
                         status="In Progress", date_from=date(2026, 1, 1), date_to=date(2026, 1, 31))
    list_sql, count_sql, params = build_list_sql(f, "priority", "desc", 2, 25)
    assert "DROP" not in list_sql
    assert params["band"] == "HIGH"
    assert params["status"] == "in_progress"
    assert params["limit"] == 25 and params["offset"] == 25
    assert str(params["date_to"]) == "2026-02-01"  # inclusive end date
    assert "LIMIT" not in count_sql


def test_invalid_filters_raise():
    with pytest.raises(ValidationFailed):
        build_list_sql(ComplaintFilters(priority_band="URGENT"), "priority", "desc", 1, 20)
    with pytest.raises(ValidationFailed):
        build_list_sql(ComplaintFilters(status="done-ish"), "priority", "desc", 1, 20)


def test_page_size_is_capped():
    _, _, params = build_list_sql(ComplaintFilters(), "priority", "desc", 1, 10_000)
    assert params["limit"] == 100


def test_like_pattern_escapes_wildcards():
    assert like_pattern("50%_off") == "%50\\%\\_off%"


def test_map_sql_requires_location_and_applies_filters():
    sql, params = build_map_sql(ComplaintFilters(priority_band="LOW"))
    assert "c.location IS NOT NULL" in sql
    assert params["band"] == "LOW"
