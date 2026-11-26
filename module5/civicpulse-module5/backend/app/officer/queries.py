"""SQL builders for the officer dashboard. Standard library only: they return
(sql, params) so they can be unit-tested without a database.

All user-supplied values go through bind parameters; sort columns come from a
whitelist. Written for PostgreSQL + PostGIS against the Module 1 schema."""
from dataclasses import dataclass
from datetime import date, timedelta

from .errors import ValidationFailed
from .workflow import Status, normalize_status

NORM_STATUS = "lower(replace(replace(c.status, ' ', '_'), '-', '_'))"
BAND_RANK = "CASE upper(c.priority_band) WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 WHEN 'LOW' THEN 2 ELSE 3 END"

SORT_COLUMNS = {
    "priority": None,  # special-cased: band rank, then score
    "priority_score": "c.priority_score",
    "created_at": "c.created_at",
    "updated_at": "c.updated_at",
    "report_count": "c.report_count",
    "status": NORM_STATUS,
    "issue_type": "lower(c.issue_type)",
    "department": "lower(d.name)",
}

MAX_PAGE_SIZE = 100
PRIORITY_BANDS = {"HIGH", "MEDIUM", "LOW"}

SELECT_COLUMNS = """
    c.id, c.issue_type, {norm} AS status, c.department_id, d.name AS department_name,
    c.report_count, c.priority_score, upper(c.priority_band) AS priority_band,
    c.created_at, c.updated_at,
    ST_Y(c.location::geometry) AS latitude, ST_X(c.location::geometry) AS longitude
""".format(norm=NORM_STATUS)

FROM_CLAUSE = "FROM complaints c LEFT JOIN departments d ON d.id = c.department_id"


@dataclass
class ComplaintFilters:
    q: str | None = None
    department_id: str | None = None
    issue_type: str | None = None
    priority_band: str | None = None
    status: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    active_only: bool = False


def like_pattern(term: str) -> str:
    escaped = term.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def build_where(f: ComplaintFilters) -> tuple[str, dict]:
    clauses: list[str] = []
    params: dict = {}

    if f.q and f.q.strip():
        params["q"] = like_pattern(f.q)
        clauses.append(
            "(c.id::text ILIKE :q ESCAPE '\\' OR c.issue_type ILIKE :q ESCAPE '\\' "
            "OR c.priority_reason::text ILIKE :q ESCAPE '\\' OR d.name ILIKE :q ESCAPE '\\' "
            "OR EXISTS (SELECT 1 FROM reports r WHERE r.complaint_id = c.id AND "
            "(r.original_description ILIKE :q ESCAPE '\\' OR r.translated_description ILIKE :q ESCAPE '\\')))"
        )
    if f.department_id:
        params["department_id"] = f.department_id
        clauses.append("c.department_id::text = :department_id")
    if f.issue_type:
        params["issue_type"] = f.issue_type.strip()
        clauses.append("lower(c.issue_type) = lower(:issue_type)")
    if f.priority_band:
        band = f.priority_band.strip().upper()
        if band not in PRIORITY_BANDS:
            raise ValidationFailed("bad_priority", "Priority must be HIGH, MEDIUM or LOW.")
        params["band"] = band
        clauses.append("upper(c.priority_band) = :band")
    if f.status:
        status = normalize_status(f.status)
        if status is None:
            raise ValidationFailed("bad_status", "Unknown status filter.")
        params["status"] = status.value
        clauses.append(f"{NORM_STATUS} = :status")
    if f.active_only:
        clauses.append(f"{NORM_STATUS} NOT IN ('resolved', 'rejected')")
    if f.date_from:
        params["date_from"] = f.date_from
        clauses.append("c.created_at >= :date_from")
    if f.date_to:
        params["date_to"] = f.date_to + timedelta(days=1)  # inclusive end date
        clauses.append("c.created_at < :date_to")

    return (" WHERE " + " AND ".join(clauses)) if clauses else "", params


def build_order_by(sort_by: str, sort_dir: str) -> str:
    if sort_by not in SORT_COLUMNS:
        raise ValidationFailed("bad_sort", f"Cannot sort by '{sort_by}'.")
    direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
    if sort_by == "priority":
        # "desc" means most urgent first: HIGH band, then highest score, then oldest.
        rank_dir = "ASC" if direction == "DESC" else "DESC"
        return f"{BAND_RANK} {rank_dir}, c.priority_score {direction} NULLS LAST, c.created_at ASC, c.id"
    return f"{SORT_COLUMNS[sort_by]} {direction} NULLS LAST, c.id"


def build_list_sql(f: ComplaintFilters, sort_by: str, sort_dir: str, page: int, page_size: int):
    page = max(1, page)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    where, params = build_where(f)
    order = build_order_by(sort_by, sort_dir)
    params = {**params, "limit": page_size, "offset": (page - 1) * page_size}
    list_sql = f"SELECT {SELECT_COLUMNS} {FROM_CLAUSE}{where} ORDER BY {order} LIMIT :limit OFFSET :offset"
    count_sql = f"SELECT count(*) {FROM_CLAUSE}{where}"
    return list_sql, count_sql, params


def build_map_sql(f: ComplaintFilters, limit: int = 5000):
    where, params = build_where(f)
    extra = "c.location IS NOT NULL"
    where = f"{where} AND {extra}" if where else f" WHERE {extra}"
    sql = (
        "SELECT c.id, c.issue_type, "
        f"{NORM_STATUS} AS status, upper(c.priority_band) AS priority_band, c.priority_score, c.report_count, "
        "ST_Y(c.location::geometry) AS latitude, ST_X(c.location::geometry) AS longitude "
        f"{FROM_CLAUSE}{where} ORDER BY {BAND_RANK}, c.priority_score DESC NULLS LAST LIMIT :limit"
    )
    return sql, {**params, "limit": min(limit, 10000)}


STATS_SQL = f"""
SELECT
  count(*) AS total,
  count(*) FILTER (WHERE {NORM_STATUS} IN ('submitted', 'assigned')) AS pending,
  count(*) FILTER (WHERE {NORM_STATUS} = 'in_progress') AS in_progress,
  count(*) FILTER (WHERE {NORM_STATUS} = 'resolved') AS resolved,
  count(*) FILTER (WHERE upper(c.priority_band) = 'HIGH'
                   AND {NORM_STATUS} NOT IN ('resolved', 'rejected')) AS high_priority
FROM complaints c
"""

FILTER_OPTIONS_SQL = {
    "departments": "SELECT id, name FROM departments ORDER BY name",
    "issue_types": "SELECT DISTINCT issue_type FROM complaints WHERE issue_type IS NOT NULL ORDER BY issue_type",
}
