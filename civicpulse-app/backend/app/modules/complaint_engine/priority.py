"""Priority calculation using the intelligent 5-factor geo-aware formula, plus explainable reasons."""
import math

from .constants import (
    BAND_CRITICAL,
    BAND_HIGH,
    BAND_LOW,
    BAND_MEDIUM,
    ISSUE_LABELS,
    SEVERITY_WORDS,
    KIND_FIRE_STATION,
    KIND_GOVERNMENT,
    KIND_HOSPITAL,
    KIND_MAIN_ROAD,
    KIND_MARKET,
    KIND_POLICE,
    KIND_SCHOOL,
    KIND_TRANSIT,
)
from .domain import LocationContext, PriorityResult

_PLACE_PHRASE = {
    KIND_HOSPITAL: "Hospital nearby.",
    KIND_FIRE_STATION: "Fire station nearby.",
    KIND_SCHOOL: "School or college nearby.",
    KIND_POLICE: "Police station nearby.",
    KIND_TRANSIT: "Transit / railway station nearby.",
    KIND_GOVERNMENT: "Government / civic office nearby.",
    KIND_MAIN_ROAD: "Main road nearby.",
    KIND_MARKET: "Market nearby.",
}


def band_for(score: float, severity: int, is_emergency: bool = False) -> str:
    """Determine priority band based on calibrated thresholds:
    0–29: LOW
    30–49: MEDIUM
    50–74: HIGH
    75–100: CRITICAL (or forced by emergency escalation)
    """
    if is_emergency or score >= 75.0:
        return BAND_CRITICAL
    if score >= 50.0 or severity == 4:
        return BAND_HIGH
    if score >= 30.0:
        return BAND_MEDIUM
    return BAND_LOW


def calculate_priority(
    severity: int,
    reports: int,
    days_pending: int,
    location: LocationContext,
    issue_type: str = "other",
) -> PriorityResult:
    """
    Intelligent Priority Scoring:
    - Issue severity: 30%
    - Location importance: 25%
    - Public impact: 20%
    - Duplicate complaints: 15%
    - Urgency and duration: 10%
    """
    severity = max(1, min(4, int(severity)))
    reports = max(1, int(reports))
    days_pending = max(0, int(days_pending))
    factor = max(0.0, min(1.0, float(getattr(location, "factor", 0.0))))
    is_emergency = getattr(location, "is_emergency", False)

    # 1. Severity component (30%)
    comp_sev = 0.30 * (severity / 4.0)

    # 2. Location importance component (25%)
    comp_loc = 0.25 * factor

    # 3. Public impact component (20%)
    dist_mult = 1.0
    dist_m = getattr(location, "distance_m", None)
    if dist_m is not None:
        if dist_m <= 50:
            dist_mult = 1.0
        elif dist_m <= 150:
            dist_mult = 0.8
        elif dist_m <= 300:
            dist_mult = 0.5
        elif dist_m <= 500:
            dist_mult = 0.3
        else:
            dist_mult = 0.1
    comp_impact = 0.20 * min(1.0, (factor * dist_mult) + (0.15 if reports >= 2 else 0.0))

    # 4. Duplicate complaints component (15%)
    comp_rep = 0.15 * min(1.0, math.log(1 + reports) / math.log(21))

    # 5. Urgency & unresolved duration component (10%)
    comp_age = 0.10 * min(1.0, days_pending / 14.0)

    raw_score = 100.0 * (comp_sev + comp_loc + comp_impact + comp_rep + comp_age)

    # Emergency escalation rule
    if is_emergency:
        raw_score = max(raw_score, 82.0)

    score = round(min(100.0, max(5.0, raw_score)), 2)
    band = band_for(score, severity, is_emergency)

    reasons = [f"{SEVERITY_WORDS[severity]} {ISSUE_LABELS.get(issue_type, 'civic issue')}."]
    if reports >= 2:
        reasons.append(f"{reports} citizen reports.")
    if days_pending >= 1:
        reasons.append(f"Pending for {days_pending} day{'s' if days_pending != 1 else ''}.")

    loc_name = getattr(location, "name", None)
    if loc_name and dist_m is not None:
        reasons.append(f"Located {int(dist_m)} metres from {loc_name}.")
    elif getattr(location, "kind", None):
        reasons.append(_PLACE_PHRASE.get(location.kind, f"Near {location.kind}."))
    elif factor > 0:
        reasons.append("Near an important public facility.")

    if is_emergency:
        reasons.append("EMERGENCY ESCALATION: Immediate threat to public safety / emergency facility access.")
    elif severity == 4 and score < 50:
        reasons.append("Critical severity forces HIGH priority.")

    shown = f"{round(score, 1):g}"
    text = f"{band} — {shown}/100\nReasons:\n" + "\n".join(f"- {r}" for r in reasons)

    return PriorityResult(
        score=score,
        band=band,
        reasons=reasons,
        priority_reason=text,
        components={
            "severity": round(comp_sev * 100, 2),
            "location": round(comp_loc * 100, 2),
            "public_impact": round(comp_impact * 100, 2),
            "duplicates": round(comp_rep * 100, 2),
            "urgency": round(comp_age * 100, 2),
        },
        inputs={
            "severity": severity,
            "reports": reports,
            "days_pending": days_pending,
            "location_factor": factor,
            "location_kind": getattr(location, "kind", None),
            "nearest_facility": loc_name,
            "distance_m": dist_m,
        },
        nearest_facility_name=loc_name,
        nearest_facility_type=getattr(location, "kind", None),
        nearest_facility_distance_m=dist_m,
        nearby_facilities=getattr(location, "nearby_facilities", []),
        is_emergency=is_emergency,
        citizen_urgency_reason=getattr(location, "citizen_urgency_reason", None),
    )
