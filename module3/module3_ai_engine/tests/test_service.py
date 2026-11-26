import json

from app.modules.ai_engine.fingerprint import sha256_hex
from tests.conftest import JPEG, good_json


def test_live_success_english(make_classifier):
    c, client = make_classifier(good_json())
    r = c.classify_complaint(JPEG, "Big pothole here")
    assert (r.issue_type, r.severity, r.source, r.needs_review) == ("pothole", 3, "live_ai", False)
    assert r.translated_text == "Big pothole here" and r.detected_language == "en"


def test_hindi_translation_from_model(make_classifier):
    c, _ = make_classifier(good_json(detected_language="hi", translated_text="There is a very large pothole."))
    r = c.classify_complaint(JPEG, "यहाँ सड़क पर बहुत बड़ा गड्ढा है।")
    assert r.detected_language == "hi" and r.translated_text == "There is a very large pothole."
    assert r.original_text.startswith("यहाँ")


def test_low_confidence_needs_review(make_classifier):
    c, _ = make_classifier(good_json(confidence=0.69))
    assert c.classify_complaint(JPEG, "x").needs_review is True


def test_threshold_boundary_is_normal(make_classifier):
    c, _ = make_classifier(good_json(confidence=0.70))
    assert c.classify_complaint(JPEG, "x").needs_review is False


def test_model_unclassified_needs_review(make_classifier):
    c, _ = make_classifier(good_json(issue_type="unclassified", confidence=0.95))
    assert c.classify_complaint(JPEG, "x").needs_review is True


def test_retry_once_then_success(make_classifier):
    c, client = make_classifier("garbage output", good_json())
    r = c.classify_complaint(JPEG, "x")
    assert client.calls == 2 and r.source == "live_ai"


def test_malformed_twice_returns_unclassified(make_classifier):
    c, client = make_classifier("bad", "still bad")
    r = c.classify_complaint(JPEG, "x")
    assert client.calls == 2
    assert (r.issue_type, r.needs_review, r.source) == ("unclassified", True, "fallback")


def test_api_failure_uses_saved_demo(make_classifier, api_down):
    demo = {sha256_hex(JPEG): {"issue_type": "garbage", "severity": 2, "confidence": 0.9, "reason": "Waste pile"}}
    c, _ = make_classifier(api_down, demo=demo)
    r = c.classify_complaint(JPEG, "kachra")
    assert r.source == "saved_demo" and r.issue_type == "garbage"
    assert r.reason.startswith("[Saved demo result]")


def test_api_failure_no_match_unclassified(make_classifier, api_down):
    c, _ = make_classifier(api_down)
    r = c.classify_complaint(JPEG, "x")
    assert (r.issue_type, r.needs_review, r.source) == ("unclassified", True, "fallback")


def test_empty_and_invalid_images_never_raise(make_classifier):
    c, client = make_classifier()
    assert c.classify_complaint(b"", "x").issue_type == "unclassified"
    assert c.classify_complaint(b"not an image", "x").issue_type == "unclassified"
    assert client.calls == 0


def test_unexpected_exception_is_contained(make_classifier):
    c, _ = make_classifier(RuntimeError("boom"))
    assert c.classify_complaint(JPEG, "x").source == "fallback"


def test_output_matches_contract_keys(make_classifier):
    c, _ = make_classifier(good_json())
    keys = set(json.loads(c.classify_complaint(JPEG, "x").model_dump_json()))
    assert keys == {"issue_type", "severity", "confidence", "reason", "detected_language",
                    "original_text", "translated_text", "needs_review", "source"}
