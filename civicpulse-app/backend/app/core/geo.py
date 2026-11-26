"""Small helper for PostGIS points."""
from geoalchemy2.elements import WKTElement
from app.core.config import settings


def make_point(latitude: float, longitude: float):
    """Build a PostGIS point or string representation for SQLite.

    IMPORTANT: PostGIS wants LONGITUDE first, then LATITUDE. Everywhere else in this
    project we say (latitude, longitude), so always use this helper instead of
    writing "POINT(...)" by hand.
    """
    if settings.database_url.startswith("sqlite"):
        return f"POINT({longitude} {latitude})"
    return WKTElement(f"POINT({longitude} {latitude})", srid=4326)
