"""Priority calculation using the exact agreed formula, plus explanations derived from it."""
import math

from .constants import BAND_HIGH, BAND_LOW, BAND_MEDIUM, ISSUE_LABELS, SEVERITY_WORDS
from .constants import KIND_HOSPITAL, KIND_MAIN_ROAD, KIND_MARKET, KIND_SCHOOL
from .domain import LocationContext, PriorityResult

_PLACE_PHRASE = {
    KIND_SCHOOL: "School nearby.", KIND_HOSPITAL: "Hospital nearby.",
    KIND_MAIN_ROAD: "Main road nearby.", KIND_MARKET: "Market nearby.",
}


def band_for(score: float, severity: int) -> str:
    if score >= 60 or severity == 4:
        return BAND_HIGH
    if score >= 40:
        return BAND_MEDIUM
    return BAND_LOW


def calculate_priority(severity: int, reports: int, days_pending: int,
                       location: LocationContext, issue_type: str = "other") -> PriorityResult:
    """
    score = 100 * (0.40*(severity/4) + 0.25*min(1, ln(1+reports)/ln(21))
                   + 0.20*min(1, days_pending/14) + 0.15*location_factor)
    Inputs are clamped to sane ranges: severity 1-4, reports >= 1, days >= 0.
    days_pending is whole days (floored) so the stated reason matches the calculation exactly.
    """
    severity = max(1, min(4, int(severity)))
    reports = max(1, int(reports))
    days_pending = max(0, int(days_pending))
    factor = location.factor

    comp = {
        "severity": 0.40 * (severity / 4),
        "reports": 0.25 * min(1, math.log(1 + reports) / math.log(21)),
        "age": 0.20 * min(1, days_pending / 14),
        "location": 0.15 * factor,
    }
    score = round(100 * (comp["severity"] + comp["reports"] + comp["age"] + comp["location"]), 2)
    band = band_for(score, severity)

    reasons = [f"{SEVERITY_WORDS[severity]} {ISSUE_LABELS.get(issue_type, 'civic issue')}."]
    if reports >= 2:
        reasons.append(f"{reports} citizen reports.")
    if days_pending >= 1:
        reasons.append(f"Pending for {days_pending} day{'s' if days_pending != 1 else ''}.")
    if factor > 0:
        reasons.append(_PLACE_PHRASE.get(location.kind or "", "Near a school or hospital." if factor == 1.0
                                          else "Near a main road or market."))
    if severity == 4 and score < 60:
        reasons.append("Critical severity forces HIGH priority.")

    shown = f"{round(score, 1):g}"
    text = f"{band} — {shown}/100\nReasons:\n" + "\n".join(f"- {r}" for r in reasons)
    return PriorityResult(
        score=score, band=band, reasons=reasons, priority_reason=text,
        components={k: round(v * 100, 2) for k, v in comp.items()},
        inputs={"severity": severity, "reports": reports, "days_pending": days_pending,
                "location_factor": factor, "location_kind": location.kind})
