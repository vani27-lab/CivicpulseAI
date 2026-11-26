import json

from app.modules.ai_engine.demo_store import DemoResultStore
from app.modules.ai_engine.fingerprint import sha256_hex


def test_lookup_hit_miss_and_invalid(tmp_path):
    fp = sha256_hex(b"img")
    p = tmp_path / "d.json"
    p.write_text(json.dumps({
        "_comment": "ignored",
        fp: {"issue_type": "pothole", "severity": 3, "confidence": 0.9, "reason": "r"},
        "bad": {"issue_type": "nope"},
    }))
    s = DemoResultStore(str(p))
    assert s.lookup(fp).issue_type == "pothole"
    assert s.lookup(sha256_hex(b"other")) is None
    assert s.lookup("bad") is None


def test_missing_file(tmp_path):
    assert DemoResultStore(str(tmp_path / "none.json")).lookup("abc") is None
