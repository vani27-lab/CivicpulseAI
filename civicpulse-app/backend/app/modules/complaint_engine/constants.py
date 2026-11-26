"""Constants for the Complaint Intelligence Engine (Module 4)."""

# duplicate_status values returned by POST /complaints/process
DUP_NEW = "new"
DUP_MERGED = "merged"
DUP_POSSIBLE = "possible_duplicate"

BAND_CRITICAL = "CRITICAL"
BAND_HIGH = "HIGH"
BAND_MEDIUM = "MEDIUM"
BAND_LOW = "LOW"

ISSUE_UNCLASSIFIED = "unclassified"
ISSUE_OTHER = "other"

SEVERITY_WORDS = {1: "Minor", 2: "Moderate", 3: "Serious", 4: "Critical"}
ISSUE_LABELS = {
    "pothole": "pothole",
    "road_damage": "road damage",
    "garbage": "garbage accumulation",
    "broken_streetlight": "broken streetlight",
    "blocked_drain": "blocked drain",
    "other": "civic issue",
    "unclassified": "civic issue",
}

# Place kinds understood by the location factor
KIND_SCHOOL = "school"
KIND_HOSPITAL = "hospital"
KIND_FIRE_STATION = "fire_station"
KIND_POLICE = "police"
KIND_TRANSIT = "transit"
KIND_GOVERNMENT = "government"
KIND_MAIN_ROAD = "main_road"
KIND_MARKET = "market"
