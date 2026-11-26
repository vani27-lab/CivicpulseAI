"""GPS validation."""
import math
from dataclasses import dataclass, field
from typing import List, Optional

from .config import Settings
from .exceptions import InvalidGPSError


@dataclass
class GPSCheck:
    warnings: List[str] = field(default_factory=list)
    accuracy_m: Optional[float] = None


def validate_gps(latitude, longitude, accuracy, settings: Settings) -> GPSCheck:
    """Raise InvalidGPSError for unusable coordinates; return warnings for weak-but-usable ones."""
    for name, v in (("latitude", latitude), ("longitude", longitude)):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise InvalidGPSError(f"{name} is missing or not a finite number")
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise InvalidGPSError("Coordinates out of range")
    if latitude == 0 and longitude == 0:
        raise InvalidGPSError("Coordinates (0, 0) are not a real location")
    if settings.gps_bbox_enabled:
        min_lat, min_lon, max_lat, max_lon = settings.gps_bbox
        if not (min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon):
            raise InvalidGPSError("Coordinates are outside the supported service area")

    check = GPSCheck()
    if accuracy is None:
        check.warnings.append("gps_accuracy_unknown")
    elif not isinstance(accuracy, (int, float)) or not math.isfinite(accuracy) or accuracy < 0:
        check.warnings.append("gps_accuracy_invalid")
    else:
        check.accuracy_m = float(accuracy)
        if accuracy > settings.max_gps_accuracy_m:
            check.warnings.append("low_gps_accuracy")
    return check
