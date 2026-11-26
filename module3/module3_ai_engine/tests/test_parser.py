import json

import pytest

from app.modules.ai_engine.exceptions import MalformedAIResponse
from app.modules.ai_engine.parser import parse_ai_response

BASE = {"issue_type": "garbage", "severity": 2, "confidence": 0.9, "reason": "Pile of waste"}


def test_valid():
    r = parse_ai_response(json.dumps(BASE))
    assert (r.issue_type, r.severity, r.confidence) == ("garbage", 2, 0.9)


def test_code_fence_and_chatter_tolerated():
    r = parse_ai_response("Here you go:\n```json\n" + json.dumps(BASE) + "\n```")
    assert r.issue_type == "garbage"


def test_issue_type_normalised():
    assert parse_ai_response(json.dumps({**BASE, "issue_type": " Pothole "})).issue_type == "pothole"


@pytest.mark.parametrize("bad", [
    "", "not json", "{broken", "[]",
    json.dumps({**BASE, "issue_type": "flood"}),
    json.dumps({**BASE, "severity": 0}),
    json.dumps({**BASE, "severity": 5}),
    json.dumps({**BASE, "severity": 2.5}),
    json.dumps({**BASE, "severity": True}),
    json.dumps({**BASE, "confidence": 1.2}),
    json.dumps({**BASE, "confidence": "high"}),
    json.dumps({**BASE, "reason": "  "}),
    json.dumps({k: v for k, v in BASE.items() if k != "severity"}),
])
def test_rejects_malformed(bad):
    with pytest.raises(MalformedAIResponse):
        parse_ai_response(bad)
