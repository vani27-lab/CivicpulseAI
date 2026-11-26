"""Geospatially intelligent facility detection and impact analysis.

Queries OpenStreetMap data (Overpass API) with local caching, distance
calculation in metres, facility categorization, impact multiplier weighting,
and emergency escalation detection.
"""
import json
import logging
import math
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Facility Categories
CAT_HOSPITAL = "hospital"
CAT_SCHOOL = "school"
CAT_FIRE_STATION = "fire_station"
CAT_POLICE = "police"
CAT_TRANSIT = "transit"
CAT_GOVERNMENT = "government"
CAT_MAIN_ROAD = "main_road"
CAT_MARKET = "market"

FACILITY_LABELS = {
    CAT_HOSPITAL: "Hospital / Healthcare",
    CAT_SCHOOL: "School / Educational Institution",
    CAT_FIRE_STATION: "Fire & Rescue Station",
    CAT_POLICE: "Police Station",
    CAT_TRANSIT: "Railway / Transit Hub",
    CAT_GOVERNMENT: "Government / Municipal Office",
    CAT_MAIN_ROAD: "Main Arterial Road",
    CAT_MARKET: "Commercial Market Area",
}

# Built-in Civic Landmarks Seed Database
# Covers Mathura / Delhi-NCR / Urban Civic zones used in demo and tests
SEED_FACILITIES = [
    # Mathura Area (around 27.48 to 27.61, 77.58 to 77.69)
    {"name": "District Hospital Mathura", "type": CAT_HOSPITAL, "lat": 27.4932, "lon": 77.6740},
    {"name": "City Civil Hospital & Trauma Centre", "type": CAT_HOSPITAL, "lat": 27.5048, "lon": 77.6848},
    {"name": "Lifeline Emergency Clinic", "type": CAT_HOSPITAL, "lat": 27.6030, "lon": 77.5960},
    {"name": "St. Paul's Senior Secondary School", "type": CAT_SCHOOL, "lat": 27.4940, "lon": 77.6750},
    {"name": "Government Girls Inter College", "type": CAT_SCHOOL, "lat": 27.5020, "lon": 77.6810},
    {"name": "Delhi Public School Campus", "type": CAT_SCHOOL, "lat": 27.6050, "lon": 77.5940},
    {"name": "Mathura Central Fire Station", "type": CAT_FIRE_STATION, "lat": 27.4910, "lon": 77.6720},
    {"name": "Industrial Area Fire & Rescue Post", "type": CAT_FIRE_STATION, "lat": 27.5060, "lon": 77.6860},
    {"name": "Kotwali Central Police Station", "type": CAT_POLICE, "lat": 27.4950, "lon": 77.6760},
    {"name": "Civil Lines Police Station", "type": CAT_POLICE, "lat": 27.5010, "lon": 77.6830},
    {"name": "Mathura Junction Railway Station", "type": CAT_TRANSIT, "lat": 27.4820, "lon": 77.6690},
    {"name": "Interstate Bus Terminal (ISBT)", "type": CAT_TRANSIT, "lat": 27.4980, "lon": 77.6790},
    {"name": "Municipal Corporation Headquarters (Nagar Nigam)", "type": CAT_GOVERNMENT, "lat": 27.4960, "lon": 77.6770},
    {"name": "District Collectorate & Magistrate Office", "type": CAT_GOVERNMENT, "lat": 27.5000, "lon": 77.6800},
    {"name": "Vikas Bhawan Administrative Complex", "type": CAT_GOVERNMENT, "lat": 27.5070, "lon": 77.6835},
    {"name": "Grand Trunk Main Road Junction", "type": CAT_MAIN_ROAD, "lat": 27.4900, "lon": 77.6710},
    {"name": "Chhatta Commercial Market Complex", "type": CAT_MARKET, "lat": 27.4970, "lon": 77.6755},
]


@dataclass
class FacilityRecord:
    name: str
    facility_type: str
    distance_m: float
    latitude: float
    longitude: float
    source: str = "cache"
    impact_multiplier: float = 1.0


@dataclass
class GeoAnalysisResult:
    nearest_facility: Optional[FacilityRecord]
    nearby_facilities: List[FacilityRecord]
    location_factor: float
    is_emergency: bool
    public_impact_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    impact_explanation: str
    citizen_urgency_reason: str
    reasons: List[str] = field(default_factory=list)


def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two coordinates in metres."""
    r = 6371000.0  # Earth's mean radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 1)


def get_facility_impact_multiplier(issue_type: str, facility_type: str) -> float:
    """Calculate the specific impact multiplier based on issue category and facility type.
    
    A dangerous road blockage near a hospital entrance or fire station deserves
    far more priority than an unrelated minor issue elsewhere.
    """
    it = (issue_type or "").lower()
    ft = (facility_type or "").lower()

    if ft == CAT_HOSPITAL:
        if any(w in it for w in ["pothole", "road", "block"]):
            return 2.0  # Ambulance blockage / critical emergency access
        if any(w in it for w in ["drain", "water", "sewage"]):
            return 1.8  # Biohazard / contamination near hospital
        if "garbage" in it:
            return 1.4  # Hygiene hazard near patients
        return 1.3

    if ft == CAT_FIRE_STATION:
        if any(w in it for w in ["pothole", "road", "block", "water"]):
            return 1.9  # Fire engine dispatch obstruction
        return 1.2

    if ft == CAT_SCHOOL:
        if any(w in it for w in ["pothole", "road", "block"]):
            return 1.5  # Child pedestrian safety / school buses
        if any(w in it for w in ["drain", "water", "sewage"]):
            return 1.5  # Disease vector / school children safety
        if "streetlight" in it:
            return 1.4  # Early morning / evening child safety
        if "garbage" in it:
            return 1.3
        return 1.2

    if ft == CAT_TRANSIT:
        if any(w in it for w in ["pothole", "road", "drain", "water"]):
            return 1.5  # High-volume pedestrian and commuter disruption
        if "streetlight" in it:
            return 1.4
        return 1.2

    if ft in (CAT_GOVERNMENT, CAT_POLICE):
        if any(w in it for w in ["pothole", "road"]):
            return 1.3
        return 1.1

    if ft in (CAT_MAIN_ROAD, CAT_MARKET):
        return 1.2

    return 1.0


def query_overpass_osm(lat: float, lon: float, radius_m: int = 600) -> List[dict]:
    """Query OpenStreetMap Overpass API for facilities around coordinates.
    
    Returns list of facility dicts or empty list on network error/timeout.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:4];
    (
      node["amenity"~"hospital|clinic|doctors|school|college|university|fire_station|police|townhall"](around:{radius_m},{lat},{lon});
      way["amenity"~"hospital|clinic|doctors|school|college|university|fire_station|police|townhall"](around:{radius_m},{lat},{lon});
      node["railway"="station"](around:{radius_m},{lat},{lon});
      way["railway"="station"](around:{radius_m},{lat},{lon});
      node["office"="government"](around:{radius_m},{lat},{lon});
      way["office"="government"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    try:
        data = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(overpass_url, data=data, headers={"User-Agent": "CivicPulseAI/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                results = []
                for el in body.get("elements", []):
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("operator") or tags.get("ref")
                    amenity = tags.get("amenity", "")
                    railway = tags.get("railway", "")
                    office = tags.get("office", "")

                    if amenity in ("hospital", "clinic", "doctors"):
                        ftype = CAT_HOSPITAL
                    elif amenity in ("school", "college", "university"):
                        ftype = CAT_SCHOOL
                    elif amenity == "fire_station":
                        ftype = CAT_FIRE_STATION
                    elif amenity == "police":
                        ftype = CAT_POLICE
                    elif railway == "station":
                        ftype = CAT_TRANSIT
                    elif office == "government" or amenity == "townhall":
                        ftype = CAT_GOVERNMENT
                    else:
                        continue

                    e_lat = el.get("lat") or (el.get("center", {}).get("lat"))
                    e_lon = el.get("lon") or (el.get("center", {}).get("lon"))
                    if e_lat and e_lon:
                        results.append({
                            "name": name or f"Local {FACILITY_LABELS.get(ftype, 'Facility')}",
                            "type": ftype,
                            "lat": float(e_lat),
                            "lon": float(e_lon),
                            "source": "osm_overpass",
                        })
                return results
    except Exception as e:
        logger.debug("Overpass API query skipped or timed out: %s", e)
    return []


def get_cached_facilities(db, lat: float, lon: float, radius_m: int = 1500) -> List[dict]:
    """Retrieve facilities from database facility_cache table if available."""
    if db is None:
        return []
    try:
        from sqlalchemy import text
        # Bounding box filter (1 deg lat ~ 111km, 0.015 deg ~ 1.6km)
        d_deg = radius_m / 111000.0
        rows = db.execute(
            text(
                "SELECT name, facility_type, latitude, longitude, source FROM facility_cache "
                "WHERE latitude BETWEEN :min_lat AND :max_lat "
                "AND longitude BETWEEN :min_lon AND :max_lon"
            ),
            {
                "min_lat": lat - d_deg,
                "max_lat": lat + d_deg,
                "min_lon": lon - d_deg,
                "max_lon": lon + d_deg,
            }
        ).fetchall()
        return [
            {
                "name": r[0],
                "type": r[1],
                "lat": float(r[2]),
                "lon": float(r[3]),
                "source": r[4],
            }
            for r in rows
        ]
    except Exception as e:
        logger.debug("Database facility cache check bypassed: %s", e)
        return []


def save_facilities_to_cache(db, facilities: List[dict]):
    """Save newly discovered facilities to DB cache table."""
    if db is None or not facilities:
        return
    try:
        from sqlalchemy import text
        for f in facilities:
            db.execute(
                text(
                    "INSERT INTO facility_cache (name, facility_type, latitude, longitude, source) "
                    "VALUES (:name, :type, :lat, :lon, :source)"
                ),
                {
                    "name": f["name"],
                    "type": f["type"],
                    "lat": f["lat"],
                    "lon": f["lon"],
                    "source": f.get("source", "osm_cache"),
                }
            )
        db.commit()
    except Exception as e:
        logger.debug("Could not commit facilities to DB cache: %s", e)


def analyze_geospatial_impact(
    lat: float,
    lon: float,
    issue_type: str = "pothole",
    severity: int = 1,
    db=None,
    max_search_radius_m: int = 1000,
) -> GeoAnalysisResult:
    """Analyze nearby facilities and calculate geospatial public impact.
    
    Returns structured GeoAnalysisResult with nearest facility, distance,
    impact factor, emergency flags, and transparent reasons.
    """
    candidates: List[dict] = []

    # 1. Try DB facility cache
    candidates.extend(get_cached_facilities(db, lat, lon, max_search_radius_m))

    # 2. Add Local Seed Facilities
    candidates.extend(SEED_FACILITIES)

    # 3. If no nearby facility found in seed or cache, query live Overpass OSM
    has_nearby = any(haversine_distance_m(lat, lon, c["lat"], c["lon"]) <= max_search_radius_m for c in candidates)
    if not has_nearby:
        live_osm = query_overpass_osm(lat, lon, max_search_radius_m)
        if live_osm:
            candidates.extend(live_osm)
            save_facilities_to_cache(db, live_osm)

    # 4. Deduplicate candidates by name and compute precise Haversine distance
    seen_keys = set()
    nearby: List[FacilityRecord] = []

    for c in candidates:
        key = (c["name"].strip().lower(), c["type"])
        if key in seen_keys:
            continue
        seen_keys.add(key)

        dist = haversine_distance_m(lat, lon, c["lat"], c["lon"])
        if dist <= max_search_radius_m:
            mult = get_facility_impact_multiplier(issue_type, c["type"])
            nearby.append(
                FacilityRecord(
                    name=c["name"],
                    facility_type=c["type"],
                    distance_m=dist,
                    latitude=c["lat"],
                    longitude=c["lon"],
                    source=c.get("source", "local_seed"),
                    impact_multiplier=mult,
                )
            )

    # Sort primarily by proximity, secondarily by impact multiplier
    nearby.sort(key=lambda f: f.distance_m / max(0.8, f.impact_multiplier))

    nearest = nearby[0] if nearby else None

    # 5. Compute Location Factor (0.0 to 1.0 for the priority formula)
    # Distance decay:
    # <= 50m: 1.0
    # 51 - 150m: 0.8
    # 151 - 300m: 0.5
    # 301 - 500m: 0.3
    # > 500m: 0.0
    location_factor = 0.0
    is_emergency = False
    reasons = []

    if nearest:
        dist = nearest.distance_m
        if dist <= 50.0:
            dist_factor = 1.0
        elif dist <= 150.0:
            dist_factor = 0.8
        elif dist <= 300.0:
            dist_factor = 0.5
        elif dist <= 500.0:
            dist_factor = 0.3
        else:
            dist_factor = 0.1

        # Multiply distance factor by the issue-specific facility importance multiplier
        raw_factor = dist_factor * (nearest.impact_multiplier / 1.5)
        location_factor = round(min(1.0, max(0.1, raw_factor)), 2)

        facility_label = FACILITY_LABELS.get(nearest.facility_type, nearest.facility_type)
        reasons.append(f"Located {int(dist)} metres from {nearest.name} ({facility_label}).")

        # 6. Emergency Escalation Rules
        # Rule A: Severity 4 (Critical) within 100m of Hospital or Fire Station
        if severity >= 4 and nearest.facility_type in (CAT_HOSPITAL, CAT_FIRE_STATION) and dist <= 100.0:
            is_emergency = True
            reasons.append("EMERGENCY ESCALATION: Critical threat adjacent to emergency healthcare / rescue facility.")

        # Rule B: Severity >= 3 road blockage/pothole within 50m of Hospital entrance or Fire Station
        elif severity >= 3 and nearest.facility_type in (CAT_HOSPITAL, CAT_FIRE_STATION) and dist <= 50.0:
            is_emergency = True
            reasons.append(f"EMERGENCY ESCALATION: Dangerous {issue_type} directly obstructing {nearest.name} entrance.")

        # Rule C: Severity 4 within 50m of a School
        elif severity >= 4 and nearest.facility_type == CAT_SCHOOL and dist <= 50.0:
            is_emergency = True
            reasons.append(f"EMERGENCY ESCALATION: Severe hazard directly outside {nearest.name}.")

        # Add potential impact explanation
        if nearest.impact_multiplier >= 1.8:
            reasons.append("Critical potential impact on emergency patient transport and life-safety operations.")
        elif nearest.impact_multiplier >= 1.4:
            reasons.append("High potential impact on public movement, children safety, or pedestrian density.")
        elif nearest.impact_multiplier >= 1.2:
            reasons.append("Moderate impact on civic accessibility and daily municipal traffic.")
    else:
        location_factor = 0.0
        reasons.append("No critical public facilities detected within 1 km.")

    # Determine Public Impact Level
    if is_emergency:
        impact_level = "CRITICAL"
    elif location_factor >= 0.7:
        impact_level = "HIGH"
    elif location_factor >= 0.4:
        impact_level = "MEDIUM"
    else:
        impact_level = "LOW"

    # Impact Explanation
    if nearest:
        impact_exp = f"{impact_level} Impact — {int(nearest.distance_m)}m from {nearest.name}"
        citizen_urgency = f"Marked urgent: Located {int(nearest.distance_m)}m from {nearest.name}"
    else:
        impact_exp = "Standard civic zone (no immediate critical facility impacted)"
        citizen_urgency = "Standard municipal queue"

    return GeoAnalysisResult(
        nearest_facility=nearest,
        nearby_facilities=nearby[:6],  # top 6 closest
        location_factor=location_factor,
        is_emergency=is_emergency,
        public_impact_level=impact_level,
        impact_explanation=impact_exp,
        citizen_urgency_reason=citizen_urgency,
        reasons=reasons,
    )
