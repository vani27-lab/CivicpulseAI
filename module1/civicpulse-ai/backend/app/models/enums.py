"""Fixed lists of allowed values, shared by the database and the API."""
import enum

from sqlalchemy import Enum


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    OFFICER = "officer"
    ADMIN = "admin"


class ComplaintCategory(str, enum.Enum):
    POTHOLE = "pothole"          # also covers damaged roads
    GARBAGE = "garbage"
    STREETLIGHT = "streetlight"
    DRAINAGE = "drainage"        # blocked drains
    OTHER = "other"
    UNCLASSIFIED = "unclassified"  # AI could not decide -> officer review


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class PriorityLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DuplicateStatus(str, enum.Enum):
    NONE = "none"          # first report of a problem
    MERGED = "merged"      # confirmed duplicate (distance AND image match)
    POSSIBLE = "possible"  # uncertain match, officer should check


def enum_type(enum_class: type[enum.Enum]) -> Enum:
    """Store an enum as plain text (VARCHAR) holding the lower-case value.

    Plain text is easier to change later than a native PostgreSQL enum.
    """
    return Enum(
        enum_class,
        native_enum=False,
        length=20,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )
