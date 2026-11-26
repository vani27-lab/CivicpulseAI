"""PostgreSQL + PostGIS repository (SQLAlchemy 2.x, synchronous Session, raw SQL via text()).

Assumes the agreed schema from the project README: UUID primary keys, complaints.location is
geography(Point, 4326), reports.image_embedding holds the CLIP vector.

NOT TESTED against a real database in the environment that generated this module. Run it against a
Module 1 database before relying on it.

Embedding column type is unknown (ARRAY(float8)? pgvector?). Pass `embedding_to_db` / `embedding_from_db`
to adapt, e.g. for pgvector: to_db=lambda v: "[" + ",".join(map(str, v)) + "]" together with a ::vector cast
in your own subclass. Default: lists are passed as-is (works for float8[]).
"""
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from .domain import Candidate, ComplaintRecord, NewReport, ReportRecord


def _default_from_db(value: Any) -> Optional[List[float]]:
    if value is None:
        return None
    if isinstance(value, str):  # pgvector text form "[0.1,0.2]"
        try:
            value = json.loads(value)
        except ValueError:
            return None
    try:
        return [float(x) for x in value]
    except (TypeError, ValueError):
        return None


class SqlAlchemyComplaintRepository:
    def __init__(self, session: Session,
                 embedding_to_db: Callable[[Sequence[float]], Any] = lambda v: list(v),
                 embedding_from_db: Callable[[Any], Optional[List[float]]] = _default_from_db):
        self.s = session
        self._to_db = embedding_to_db
        self._from_db = embedding_from_db

    # ---- reads -----------------------------------------------------------
    def find_candidates(self, issue_type, latitude, longitude, radius_m, created_after, statuses,
                        exclude_complaint_id=None) -> List[Candidate]:
        sql = text("""
            SELECT c.id, c.issue_type, c.status, c.report_count, c.created_at,
                   ST_Y(c.location::geometry) AS lat, ST_X(c.location::geometry) AS lon
            FROM complaints c
            WHERE c.issue_type = :issue_type
              AND c.status IN :statuses
              AND c.created_at >= :created_after
              AND ST_DWithin(c.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)
              AND (CAST(:exclude AS uuid) IS NULL OR c.id <> CAST(:exclude AS uuid))
            ORDER BY ST_Distance(c.location, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography)
        """).bindparams(bindparam("statuses", expanding=True))
        rows = self.s.execute(sql, dict(issue_type=issue_type, statuses=list(statuses), created_after=created_after,
                                        lon=longitude, lat=latitude, radius=radius_m,
                                        exclude=str(exclude_complaint_id) if exclude_complaint_id else None)).all()
        return [Candidate(r.id, r.issue_type, r.status, r.report_count, r.created_at, r.lat, r.lon) for r in rows]

    def get_embeddings(self, complaint_ids) -> Dict[UUID, List[List[float]]]:
        out: Dict[UUID, List[List[float]]] = {cid: [] for cid in complaint_ids}
        if not out:
            return out
        sql = text("SELECT complaint_id, image_embedding FROM reports "
                   "WHERE complaint_id IN :ids AND image_embedding IS NOT NULL"
                   ).bindparams(bindparam("ids", expanding=True))
        for r in self.s.execute(sql, {"ids": list(complaint_ids)}):
            vec = self._from_db(r.image_embedding)
            if vec:
                out[r.complaint_id].append(vec)
        return out

    def get_complaint(self, complaint_id) -> Optional[ComplaintRecord]:
        r = self.s.execute(text("""
            SELECT c.id, c.issue_type, c.status, c.report_count, c.created_at,
                   ST_Y(c.location::geometry) AS lat, ST_X(c.location::geometry) AS lon,
                   c.department_id, c.priority_score, c.priority_band,
                   (SELECT MAX(r.ai_severity) FROM reports r WHERE r.complaint_id = c.id) AS max_severity
            FROM complaints c WHERE c.id = :id"""), {"id": complaint_id}).first()
        if r is None:
            return None
        return ComplaintRecord(r.id, r.issue_type, r.status, r.report_count, r.created_at, r.lat, r.lon,
                               r.department_id, r.max_severity, r.priority_score, r.priority_band)

    def get_reports(self, complaint_id) -> List[ReportRecord]:
        rows = self.s.execute(text("""
            SELECT id, complaint_id, latitude, longitude, created_at, image_url, user_id, gps_accuracy,
                   ai_severity, ai_confidence
            FROM reports WHERE complaint_id = :id ORDER BY created_at"""), {"id": complaint_id}).all()
        return [ReportRecord(r.id, r.complaint_id, r.latitude, r.longitude, r.created_at, r.image_url,
                             r.user_id, r.gps_accuracy, r.ai_severity, r.ai_confidence) for r in rows]

    def get_department_id(self, name) -> Optional[UUID]:
        r = self.s.execute(text("SELECT id FROM departments WHERE lower(name) = lower(:n) LIMIT 1"),
                           {"n": name}).first()
        return r.id if r else None

    def list_open_complaint_ids(self, statuses) -> List[UUID]:
        sql = text("SELECT id FROM complaints WHERE status IN :s").bindparams(bindparam("s", expanding=True))
        return [r.id for r in self.s.execute(sql, {"s": list(statuses)})]

    # ---- writes ----------------------------------------------------------
    def insert_complaint(self, complaint_id, issue_type, status, latitude, longitude, department_id, created_at):
        self.s.execute(text("""
            INSERT INTO complaints (id, issue_type, status, location, department_id, report_count,
                                    priority_score, priority_band, priority_reason, created_at, updated_at)
            VALUES (:id, :t, :st, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :dept, 0,
                    0, 'LOW', '', :ts, :ts)"""),
                       dict(id=complaint_id, t=issue_type, st=status, lon=longitude, lat=latitude,
                            dept=department_id, ts=created_at))

    def upsert_report(self, report: NewReport) -> UUID:
        import uuid as _uuid
        params = dict(
            cid=report.complaint_id, uid=report.user_id, url=report.image_url,
            od=report.original_description, td=report.translated_description,
            lat=report.latitude, lon=report.longitude, acc=report.gps_accuracy,
            conf=report.ai_confidence, sev=report.ai_severity,
            emb=self._to_db(report.embedding) if report.embedding is not None else None,
            ts=report.created_at)
        if report.report_id is not None:  # Module 2 already created the row: attach + enrich it
            params["id"] = report.report_id
            self.s.execute(text("""
                UPDATE reports SET complaint_id = :cid, translated_description = :td,
                       ai_confidence = :conf, ai_severity = :sev, image_embedding = :emb
                WHERE id = :id"""), params)
            return report.report_id
        rid = _uuid.uuid4()
        params["id"] = rid
        self.s.execute(text("""
            INSERT INTO reports (id, complaint_id, user_id, image_url, original_description,
                translated_description, latitude, longitude, gps_accuracy, ai_confidence, ai_severity,
                image_embedding, created_at)
            VALUES (:id, :cid, :uid, :url, :od, :td, :lat, :lon, :acc, :conf, :sev, :emb, :ts)"""), params)
        return rid

    def move_reports(self, report_ids, to_complaint_id):
        sql = text("UPDATE reports SET complaint_id = :to WHERE id IN :ids").bindparams(
            bindparam("ids", expanding=True))
        self.s.execute(sql, {"to": to_complaint_id, "ids": list(report_ids)})

    def refresh_report_count(self, complaint_id) -> int:
        return self.s.execute(text("""
            UPDATE complaints SET report_count = (SELECT COUNT(*) FROM reports WHERE complaint_id = :id)
            WHERE id = :id RETURNING report_count"""), {"id": complaint_id}).scalar_one()

    def update_complaint_priority(self, complaint_id, score, band, reason, updated_at):
        self.s.execute(text("""
            UPDATE complaints SET priority_score = :s, priority_band = :b, priority_reason = :r,
                   updated_at = :ts WHERE id = :id"""),
                       dict(s=score, b=band, r=reason, ts=updated_at, id=complaint_id))

    def add_status_history(self, complaint_id, officer_id, old_status, new_status, comment, created_at):
        import uuid as _uuid
        self.s.execute(text("""
            INSERT INTO status_history (id, complaint_id, officer_id, old_status, new_status, comment, created_at)
            VALUES (:id, :cid, :oid, :old, :new, :c, :ts)"""),
                       dict(id=_uuid.uuid4(), cid=complaint_id, oid=officer_id, old=old_status, new=new_status,
                            c=comment, ts=created_at))

    def commit(self): self.s.commit()
    def rollback(self): self.s.rollback()
