"""In-memory repository: used by the unit tests and for running without Postgres. Not for production."""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Sequence
from uuid import UUID

from .domain import Candidate, ComplaintRecord, NewReport, ReportRecord
from .places import haversine_m


class InMemoryComplaintRepository:
    def __init__(self, departments: Optional[Dict[str, UUID]] = None):
        self.complaints: Dict[UUID, dict] = {}
        self.reports: Dict[UUID, dict] = {}
        self.departments = {k.lower(): v for k, v in (departments or {}).items()}
        self.history: List[dict] = []
        self.commits = 0
        self.rollbacks = 0

    def find_candidates(self, issue_type, latitude, longitude, radius_m, created_after, statuses,
                        exclude_complaint_id=None) -> List[Candidate]:
        out = []
        for cid, c in self.complaints.items():
            if cid == exclude_complaint_id or c["issue_type"] != issue_type or c["status"] not in statuses:
                continue
            if c["created_at"] < created_after:
                continue
            if haversine_m(latitude, longitude, c["lat"], c["lon"]) <= radius_m:
                out.append(Candidate(cid, c["issue_type"], c["status"], self._count(cid),
                                     c["created_at"], c["lat"], c["lon"]))
        return out

    def _count(self, cid) -> int:
        return sum(1 for r in self.reports.values() if r["complaint_id"] == cid)

    def get_embeddings(self, complaint_ids) -> Dict[UUID, List[List[float]]]:
        out: Dict[UUID, List[List[float]]] = {cid: [] for cid in complaint_ids}
        for r in self.reports.values():
            if r["complaint_id"] in out and r["embedding"] is not None:
                out[r["complaint_id"]].append(list(r["embedding"]))
        return out

    def get_complaint(self, complaint_id) -> Optional[ComplaintRecord]:
        c = self.complaints.get(complaint_id)
        if c is None:
            return None
        sevs = [r["ai_severity"] for r in self.reports.values()
                if r["complaint_id"] == complaint_id and r["ai_severity"] is not None]
        return ComplaintRecord(complaint_id, c["issue_type"], c["status"], c["report_count"], c["created_at"],
                               c["lat"], c["lon"], c["department_id"], max(sevs) if sevs else None,
                               c.get("priority_score"), c.get("priority_band"))

    def get_reports(self, complaint_id) -> List[ReportRecord]:
        rows = [r for r in self.reports.values() if r["complaint_id"] == complaint_id]
        rows.sort(key=lambda r: r["created_at"])
        return [ReportRecord(r["id"], r["complaint_id"], r["latitude"], r["longitude"], r["created_at"],
                             r["image_url"], r["user_id"], r["gps_accuracy"], r["ai_severity"], r["ai_confidence"])
                for r in rows]

    def insert_complaint(self, complaint_id, issue_type, status, latitude, longitude, department_id, created_at):
        self.complaints[complaint_id] = dict(issue_type=issue_type, status=status, lat=latitude, lon=longitude,
                                             department_id=department_id, created_at=created_at, report_count=0,
                                             priority_score=0.0, priority_band="LOW", priority_reason="")

    def upsert_report(self, report: NewReport) -> UUID:
        rid = report.report_id or uuid.uuid4()
        self.reports[rid] = dict(
            id=rid, complaint_id=report.complaint_id, user_id=report.user_id, image_url=report.image_url,
            latitude=report.latitude, longitude=report.longitude, gps_accuracy=report.gps_accuracy,
            ai_confidence=report.ai_confidence, ai_severity=report.ai_severity,
            embedding=list(report.embedding) if report.embedding is not None else None,
            created_at=report.created_at, original_description=report.original_description,
            translated_description=report.translated_description)
        return rid

    def move_reports(self, report_ids, to_complaint_id):
        for rid in report_ids:
            self.reports[rid]["complaint_id"] = to_complaint_id

    def refresh_report_count(self, complaint_id) -> int:
        n = self._count(complaint_id)
        self.complaints[complaint_id]["report_count"] = n
        return n

    def update_complaint_priority(self, complaint_id, score, band, reason, updated_at):
        self.complaints[complaint_id].update(priority_score=score, priority_band=band,
                                             priority_reason=reason, updated_at=updated_at)

    def get_department_id(self, name) -> Optional[UUID]:
        return self.departments.get(name.lower())

    def add_status_history(self, complaint_id, officer_id, old_status, new_status, comment, created_at):
        self.history.append(dict(complaint_id=complaint_id, officer_id=officer_id, old_status=old_status,
                                 new_status=new_status, comment=comment, created_at=created_at))

    def list_open_complaint_ids(self, statuses) -> List[UUID]:
        return [cid for cid, c in self.complaints.items() if c["status"] in statuses]

    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1
