"""Configuration. Every threshold is configurable; nothing is hardcoded in logic."""
import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

DEFAULT_DEPARTMENT_MAP: Dict[str, str] = {
    "pothole": "Roads",
    "road_damage": "Roads",
    "garbage": "Sanitation",
    "broken_streetlight": "Electrical",
    "blocked_drain": "Drainage",
    "unclassified": "Manual review",
    "other": "Manual review",  # not in the agreed routing table; routed to manual review
}


def _csv(name: str, default: Tuple[str, ...]) -> Tuple[str, ...]:
    raw = os.getenv(name)
    return tuple(s.strip() for s in raw.split(",") if s.strip()) if raw else default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # duplicate detection
    duplicate_radius_m: float = 50.0
    duplicate_window_days: int = 30
    eligible_statuses: Tuple[str, ...] = ("submitted", "acknowledged", "in_progress")
    # image similarity (cosine). NOT calibrated on real data: tune before trusting auto-merge.
    merge_similarity_threshold: float = 0.92
    possible_similarity_threshold: float = 0.85
    merge_unclassified: bool = False
    # GPS
    max_gps_accuracy_m: float = 100.0           # above this: warning only
    max_accuracy_for_auto_merge_m: float = 50.0  # above this: never auto-merge
    gps_bbox_enabled: bool = True
    gps_bbox: Tuple[float, float, float, float] = (6.0, 68.0, 38.0, 98.0)  # min_lat,min_lon,max_lat,max_lon (India)
    # location factor
    poi_radius_m: float = 200.0           # schools & hospitals
    road_market_radius_m: float = 100.0   # main roads & markets
    places_path: str = "data/places.json"
    # complaints
    new_complaint_status: str = "submitted"
    department_map: Dict[str, str] = field(default_factory=lambda: dict(DEFAULT_DEPARTMENT_MAP))
    officer_roles: Tuple[str, ...] = ("officer", "admin")
    max_image_bytes: int = 10 * 1024 * 1024
    clip_model_name: str = "clip-ViT-B-32"

    @classmethod
    def from_env(cls) -> "Settings":
        d = cls()
        bbox = os.getenv("CP_GPS_BBOX")
        return cls(
            duplicate_radius_m=float(os.getenv("CP_DUPLICATE_RADIUS_M", d.duplicate_radius_m)),
            duplicate_window_days=int(os.getenv("CP_DUPLICATE_WINDOW_DAYS", d.duplicate_window_days)),
            eligible_statuses=_csv("CP_ELIGIBLE_STATUSES", d.eligible_statuses),
            merge_similarity_threshold=float(os.getenv("CP_MERGE_SIMILARITY", d.merge_similarity_threshold)),
            possible_similarity_threshold=float(os.getenv("CP_POSSIBLE_SIMILARITY", d.possible_similarity_threshold)),
            merge_unclassified=_bool("CP_MERGE_UNCLASSIFIED", d.merge_unclassified),
            max_gps_accuracy_m=float(os.getenv("CP_MAX_GPS_ACCURACY_M", d.max_gps_accuracy_m)),
            max_accuracy_for_auto_merge_m=float(os.getenv("CP_MAX_ACCURACY_AUTO_MERGE_M", d.max_accuracy_for_auto_merge_m)),
            gps_bbox_enabled=_bool("CP_GPS_BBOX_ENABLED", d.gps_bbox_enabled),
            gps_bbox=tuple(float(x) for x in bbox.split(",")) if bbox else d.gps_bbox,  # type: ignore[arg-type]
            poi_radius_m=float(os.getenv("CP_POI_RADIUS_M", d.poi_radius_m)),
            road_market_radius_m=float(os.getenv("CP_ROAD_MARKET_RADIUS_M", d.road_market_radius_m)),
            places_path=os.getenv("CP_PLACES_PATH", d.places_path),
            new_complaint_status=os.getenv("CP_NEW_COMPLAINT_STATUS", d.new_complaint_status),
            officer_roles=_csv("CP_OFFICER_ROLES", d.officer_roles),
            max_image_bytes=int(os.getenv("CP_MAX_IMAGE_BYTES", d.max_image_bytes)),
            clip_model_name=os.getenv("CP_CLIP_MODEL", d.clip_model_name),
        )
