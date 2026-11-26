"""Location factor: proximity to schools/hospitals (1.0) or main roads/markets (0.5).

The agreed schema has no places table, so places come from a JSON file (see data/places.json).
Implement PlaceProvider yourself to read from PostGIS or an API instead.
"""
import json
import logging
import math
from pathlib import Path
from typing import List, Optional, Protocol

from .config import Settings
from .constants import KIND_HOSPITAL, KIND_MAIN_ROAD, KIND_MARKET, KIND_SCHOOL
from .domain import LocationContext

logger = logging.getLogger(__name__)


class PlaceProvider(Protocol):
    def context(self, latitude: float, longitude: float) -> LocationContext: ...


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class NullPlaceProvider:
    """No place data: every location counts as 'other' (factor 0)."""
    def context(self, latitude: float, longitude: float) -> LocationContext:
        return LocationContext()


class StaticPlaceProvider:
    """In-memory points of interest. Entries: {"kind","lat","lon","name"?,"radius_m"?}."""

    def __init__(self, places: List[dict], settings: Settings):
        self._places = [p for p in places if self._valid(p)]
        self._s = settings

    @staticmethod
    def _valid(p) -> bool:
        return (isinstance(p, dict) and p.get("kind") in (KIND_SCHOOL, KIND_HOSPITAL, KIND_MAIN_ROAD, KIND_MARKET)
                and isinstance(p.get("lat"), (int, float)) and isinstance(p.get("lon"), (int, float)))

    @classmethod
    def from_file(cls, path: str, settings: Settings) -> "StaticPlaceProvider":
        try:
            raw = json.loads(Path(path).read_text(encoding="utf-8"))
            places = raw.get("places", []) if isinstance(raw, dict) else raw
        except (OSError, ValueError) as exc:
            logger.warning("Places file %s unusable (%s); location factor will be 0 everywhere", path, exc)
            places = []
        if not places:
            logger.warning("No places loaded: location_factor is 0 for every complaint")
        return cls(places, settings)

    def context(self, latitude: float, longitude: float) -> LocationContext:
        best_high: Optional[LocationContext] = None
        best_mid: Optional[LocationContext] = None
        for p in self._places:
            d = haversine_m(latitude, longitude, p["lat"], p["lon"])
            kind = p["kind"]
            if kind in (KIND_SCHOOL, KIND_HOSPITAL):
                if d <= p.get("radius_m", self._s.poi_radius_m) and (best_high is None or d < best_high.distance_m):
                    best_high = LocationContext(1.0, kind, p.get("name"), d)
            elif d <= p.get("radius_m", self._s.road_market_radius_m) and (best_mid is None or d < best_mid.distance_m):
                best_mid = LocationContext(0.5, kind, p.get("name"), d)
        return best_high or best_mid or LocationContext()
