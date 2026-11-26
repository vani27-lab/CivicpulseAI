"""SQL builders for the officer dashboard. Standard library only: they return
(sql, params) so they can be unit-tested without a database.

Compatible with PostgreSQL and SQLite.
"""
from dataclasses import dataclass
from datetime import date, timedelta

from .errors import ValidationFailed
from .workflow import Status, normalize_status

NORM_STATUS = "lower(replace(replace(c.status, ' ', '_'), '-', '_'))"
BAND_RANK = "CASE upper(COALESCE(c.priority_band, c.priority_level)) WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END"

SORT_COLUMNS = {
    "priority": None,  # special-cased: band rank, then score
    "priority_score": "c.priority_score",
    "created_at": "c.created_at",
    "updated_at": "c.updated_at",
    "report_count": "c.report_count",
    "status": NORM_STATUS,
    "issue_type": "lower(COALESCE(c.issue_type, c.category))",
    "department": "lower(d.name)",
}

MAX_PAGE_SIZE = 100
PRIORITY_BANDS = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

SELECT_COLUMNS = """
    c.id, COALESCE(c.issue_type, c.category) AS issue_type, {norm} AS status, c.department_id, d.name AS department_name,
    c.report_count, c.priority_score, upper(COALESCE(c.priority_band, c.priority_level)) AS priority_band,
    c.created_at, c.updated_at,
    c.latitude AS latitude, c.longitude AS longitude,
    c.nearest_facility_name, c.nearest_facility_type, c.nearest_facility_distance_m, c.is_emergency
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
            "(CAST(c.id AS TEXT) LIKE :q OR c.category LIKE :q "
            "OR CAST(c.priority_explanation AS TEXT) LIKE :q OR d.name LIKE :q "
            "OR EXISTS (SELECT 1 FROM reports r WHERE r.complaint_id = c.id AND "
            "(r.description_original LIKE :q OR r.description_english LIKE :q)))"
        )
    if f.department_id:
        params["department_id"] = f.department_id
        clauses.append("CAST(c.department_id AS TEXT) = :department_id")
    if f.issue_type:
        params["issue_type"] = f.issue_type.strip()
        clauses.append("lower(c.category) = lower(:issue_type)")
    if f.priority_band:
        band = f.priority_band.strip().upper()
        if band not in PRIORITY_BANDS:
            raise ValidationFailed("bad_priority", "Priority must be HIGH, MEDIUM or LOW.")
        params["band"] = band.lower()
        clauses.append("lower(c.priority_level) = :band")
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
        rank_dir = "ASC" if direction == "DESC" else "DESC"
        return f"{BAND_RANK} {rank_dir}, c.priority_score {direction}, c.created_at ASC, c.id"
    return f"{SORT_COLUMNS[sort_by]} {direction}, c.id"


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
    extra = "c.latitude IS NOT NULL"
    where = f"{where} AND {extra}" if where else f" WHERE {extra}"
    sql = (
        "SELECT c.id, c.category AS issue_type, "
        f"{NORM_STATUS} AS status, upper(c.priority_level) AS priority_band, c.priority_score, c.report_count, "
        "c.latitude AS latitude, c.longitude AS longitude "
        f"{FROM_CLAUSE}{where} ORDER BY {BAND_RANK}, c.priority_score DESC LIMIT :limit"
    )
    return sql, {**params, "limit": min(limit, 10000)}


STATS_SQL = f"""
SELECT
  count(*) AS total,
  count(CASE WHEN {NORM_STATUS} IN ('submitted', 'assigned') THEN 1 END) AS pending,
  count(CASE WHEN {NORM_STATUS} = 'in_progress' THEN 1 END) AS in_progress,
  count(CASE WHEN {NORM_STATUS} = 'resolved' THEN 1 END) AS resolved,
  count(CASE WHEN upper(COALESCE(c.priority_band, c.priority_level)) IN ('CRITICAL', 'HIGH') AND {NORM_STATUS} NOT IN ('resolved', 'rejected') THEN 1 END) AS high_priority
FROM complaints c
"""

FILTER_OPTIONS_SQL = {
    "departments": "SELECT id, name FROM departments ORDER BY name",
    "issue_types": "SELECT DISTINCT category AS issue_type FROM complaints WHERE category IS NOT NULL ORDER BY category",
}
