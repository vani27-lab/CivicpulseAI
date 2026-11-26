"""Register a saved demo result keyed by the image's SHA-256 fingerprint.

Example:
  python scripts/register_demo_result.py photo.jpg --issue-type pothole --severity 3 \
      --confidence 0.85 --reason "Large pothole on road" --translated-text "Big pothole here"
"""
import argparse
import hashlib
import json
from pathlib import Path

VALID = {"pothole", "road_damage", "garbage", "broken_streetlight", "blocked_drain", "other", "unclassified"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--issue-type", required=True, choices=sorted(VALID))
    ap.add_argument("--severity", required=True, type=int, choices=[1, 2, 3, 4])
    ap.add_argument("--confidence", required=True, type=float)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--translated-text", default="")
    ap.add_argument("--store", default="data/saved_demo_results.json")
    a = ap.parse_args()
    if not 0.0 <= a.confidence <= 1.0:
        ap.error("--confidence must be between 0 and 1")
    digest = hashlib.sha256(Path(a.image).read_bytes()).hexdigest()
    store = Path(a.store)
    data = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    data[digest] = {"issue_type": a.issue_type, "severity": a.severity, "confidence": a.confidence,
                    "reason": a.reason, "translated_text": a.translated_text}
    store.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Registered {digest}")


if __name__ == "__main__":
    main()
