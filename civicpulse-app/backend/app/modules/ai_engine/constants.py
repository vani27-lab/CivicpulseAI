"""Shared constants for the AI Intelligence Engine (Module 3)."""
from enum import Enum


class IssueType(str, Enum):
    POTHOLE = "pothole"
    ROAD_DAMAGE = "road_damage"
    GARBAGE = "garbage"
    BROKEN_STREETLIGHT = "broken_streetlight"
    BLOCKED_DRAIN = "blocked_drain"
    OTHER = "other"
    UNCLASSIFIED = "unclassified"


VALID_ISSUE_TYPES = frozenset(t.value for t in IssueType)

# Source labels returned in the `source` field of every result.
SOURCE_LIVE = "live_ai"
SOURCE_DEMO = "saved_demo"
SOURCE_FALLBACK = "fallback"  # Added by Module 3: unclassified safety-net result.

SEVERITY_MIN = 1
SEVERITY_MAX = 4

DEMO_REASON_PREFIX = "[Saved demo result] "
