from app.officer.priority import parse_reasons


def test_json_list():
    assert parse_reasons('["Serious pothole", "12 citizen reports"]') == ["Serious pothole", "12 citizen reports"]


def test_json_object_with_reasons():
    assert parse_reasons('{"reasons": ["School nearby"]}') == ["School nearby"]


def test_plain_text_bullets_and_semicolons():
    raw = "- Serious pothole\n\u2022 12 citizen reports; Pending for 9 days"
    assert parse_reasons(raw) == ["Serious pothole", "12 citizen reports", "Pending for 9 days"]


def test_empty_values():
    assert parse_reasons(None) == []
    assert parse_reasons("   ") == []
    assert parse_reasons([]) == []


def test_python_list_input():
    assert parse_reasons(["a", " ", "b"]) == ["a", "b"]
