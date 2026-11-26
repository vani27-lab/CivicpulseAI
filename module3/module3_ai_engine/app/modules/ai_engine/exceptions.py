"""Exceptions internal to Module 3. None of these escape classify_complaint()."""


class VisionAPIError(Exception):
    """The Vision AI API is unreachable, misconfigured, or returned an error."""


class MalformedAIResponse(ValueError):
    """The AI response could not be parsed or failed strict validation."""
