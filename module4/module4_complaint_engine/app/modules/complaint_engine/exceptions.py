class ComplaintEngineError(Exception):
    """Base class for Module 4 errors."""


class InvalidGPSError(ComplaintEngineError):
    """Coordinates are missing, out of range, or implausible."""


class ComplaintNotFound(ComplaintEngineError):
    pass


class SplitError(ComplaintEngineError):
    """The requested split is not allowed."""
