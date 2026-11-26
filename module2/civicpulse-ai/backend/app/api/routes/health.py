from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DbSession

router = APIRouter(tags=["Health"])


@router.get("/health")
def health(db: DbSession) -> dict:
    """Shows whether the server, the database and PostGIS are working."""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "error", "database": "unavailable", "postgis": "unknown"}

    try:
        postgis = db.execute(text("SELECT PostGIS_Version()")).scalar()
    except Exception:
        db.rollback()
        postgis = "not installed"

    return {"status": "ok", "database": "connected", "postgis": postgis}
