"""Small helper for PostGIS points."""
from geoalchemy2.elements import WKTElement


def make_point(latitude: float, longitude: float) -> WKTElement:
    """Build a PostGIS point.

    IMPORTANT: PostGIS wants LONGITUDE first, then LATITUDE. Everywhere else in this
    project we say (latitude, longitude), so always use this helper instead of
    writing "POINT(...)" by hand.
    """
    return WKTElement(f"POINT({longitude} {latitude})", srid=4326)
