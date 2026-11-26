"""Module 6 citizen routes. Mount with app.include_router(router) BEFORE any
generic /complaints/{id} route so /complaints/mine is not shadowed."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from .deps import get_db, get_current_user, user_id
from .shaping import public_history, compute_stats, norm, iso
from .translation import translate_cached

router = APIRouter(tags=["citizen-tracking"])

def _require_owned(db, cid, uid):
    ok = db.execute(text("SELECT 1 FROM reports WHERE CAST(complaint_id AS TEXT)=:c AND (CAST(user_id AS TEXT)=:u OR CAST(citizen_id AS TEXT)=:u) LIMIT 1"),
                    {"c": str(cid), "u": str(uid)}).first()
    if not ok:  # 404, not 403: don't reveal that other citizens' complaints exist
        raise HTTPException(404, "Complaint not found")

def _normalize_media_url(path: str | None) -> str | None:
    if not path:
        return None
    p = str(path).strip()
    if p.startswith("http://") or p.startswith("https://") or p.startswith("data:") or p.startswith("blob:"):
        return p
    if p.startswith("/uploads/") or p.startswith("/media/"):
        return p
    if p.startswith("uploads/"):
        return f"/{p}"
    if p.startswith("media/"):
        return f"/{p}"
    if p.startswith("/"):
        return f"/uploads{p}"
    return f"/uploads/{p}"


def _history(db, cid):
    rows = db.execute(text(
        "SELECT id, COALESCE(old_status, status) AS old_status, COALESCE(new_status, status) AS new_status, "
        "COALESCE(comment, note) AS comment, "
        "CASE WHEN (new_status = 'resolved' OR status = 'resolved') THEN COALESCE(after_photo_url, photo_path) ELSE after_photo_url END AS after_photo_url, "
        "created_at "
        "FROM status_history WHERE CAST(complaint_id AS TEXT)=:c ORDER BY created_at"
    ), {"c": str(cid)}).mappings().all()
    res = public_history(rows)
    for r in res:
        if r.get("after_photo_url"):
            r["after_photo_url"] = _normalize_media_url(r["after_photo_url"])
    return res

@router.get("/complaints/mine")
def mine(db=Depends(get_db), user=Depends(get_current_user)):
    uid = user_id(user)
    rows = db.execute(text("""
      SELECT c.id, COALESCE(c.issue_type, c.category) AS issue_type, c.status,
             COALESCE(c.priority_band, upper(c.priority_level)) AS priority_band, c.created_at,
        (SELECT COALESCE(r.image_url, r.image_path) FROM reports r
         WHERE r.complaint_id=c.id AND (CAST(r.user_id AS TEXT)=:u OR CAST(r.citizen_id AS TEXT)=:u)
         ORDER BY r.created_at LIMIT 1) AS thumbnail
      FROM complaints c
      WHERE EXISTS (
        SELECT 1 FROM reports r
        WHERE r.complaint_id=c.id AND (CAST(r.user_id AS TEXT)=:u OR CAST(r.citizen_id AS TEXT)=:u)
      )
      ORDER BY c.created_at DESC"""), {"u": str(uid)}).mappings().all()
    items = [{"id": str(r["id"]), "issue_type": r["issue_type"], "status": norm(r["status"]),
              "priority_band": r["priority_band"], "created_at": iso(r["created_at"]),
              "thumbnail": _normalize_media_url(r["thumbnail"])} for r in rows]
    return {"stats": compute_stats([i["status"] for i in items]), "items": items}

@router.get("/complaints/{cid}")
def detail(cid: str, db=Depends(get_db), user=Depends(get_current_user)):
    uid = user_id(user)
    _require_owned(db, cid, uid)
    c = db.execute(text(
        "SELECT id, COALESCE(issue_type, category) AS issue_type, status, "
        "COALESCE(priority_band, upper(priority_level)) AS priority_band, created_at, updated_at, "
        "before_photo_path, after_photo_path, "
        "citizen_urgency_reason, is_emergency, nearest_facility_name, nearest_facility_distance_m "
        "FROM complaints WHERE CAST(id AS TEXT)=:c"
    ), {"c": str(cid)}).mappings().first()
    mine_r = db.execute(text("""
      SELECT COALESCE(image_url, image_path) AS image_url,
             COALESCE(original_description, description_original) AS original_description,
             COALESCE(translated_description, description_english) AS translated_description,
             latitude, longitude
      FROM reports WHERE CAST(complaint_id AS TEXT)=:c AND (CAST(user_id AS TEXT)=:u OR CAST(citizen_id AS TEXT)=:u)
      ORDER BY created_at LIMIT 1"""),
      {"c": str(cid), "u": str(uid)}).mappings().first()
    hist = _history(db, cid)
    after = _normalize_media_url(c.get("after_photo_path")) or next((h["after_photo_url"] for h in reversed(hist) if h.get("after_photo_url")), None)
    before = _normalize_media_url(c.get("before_photo_path") or (mine_r["image_url"] if mine_r else None))
    citizen_urgency = c.get("citizen_urgency_reason")
    if not citizen_urgency and c.get("nearest_facility_name"):
        dist_str = f"{int(c['nearest_facility_distance_m'])}m" if c.get("nearest_facility_distance_m") else "nearby"
        citizen_urgency = f"Marked urgent: Located {dist_str} from {c['nearest_facility_name']}"

    return {
        "id": str(c["id"]), "issue_type": c["issue_type"], "status": norm(c["status"]),
        "priority_band": c["priority_band"], "created_at": iso(c["created_at"]), "updated_at": iso(c["updated_at"]),
        "before_photo_url": before,
        "after_photo_url": after if norm(c["status"]) == "resolved" else None,
        "original_description": mine_r["original_description"] if mine_r else "",
        "translated_description": mine_r["translated_description"] if mine_r else "",
        "latitude": mine_r["latitude"] if mine_r else None,
        "longitude": mine_r["longitude"] if mine_r else None,
        "citizen_urgency_reason": citizen_urgency,
        "is_emergency": bool(c.get("is_emergency")),
        "nearest_facility_name": c.get("nearest_facility_name"),
        "nearest_facility_distance_m": c.get("nearest_facility_distance_m"),
    }

@router.get("/complaints/{cid}/history")
def history(cid: str, db=Depends(get_db), user=Depends(get_current_user)):
    _require_owned(db, cid, user_id(user))
    return {"items": _history(db, cid)}

@router.get("/complaints/{cid}/updates")
def updates(cid: str, lang: str = Query("en", max_length=8), db=Depends(get_db), user=Depends(get_current_user)):
    """Officer comments with optional translation; failure falls back to original only."""
    _require_owned(db, cid, user_id(user))
    out = []
    for h in _history(db, cid):
        if not h["comment"]:
            continue
        out.append({"id": h["id"], "status": h["new_status"], "created_at": h["created_at"],
                    "comment": h["comment"], "comment_lang": "en",
                    "translated_comment": translate_cached(db, h["id"], h["comment"], lang),
                    "translated_lang": lang})
    return {"items": out}

@router.get("/notifications")
def notifications(unread_only: bool = False, db=Depends(get_db), user=Depends(get_current_user)):
    q = "SELECT id, complaint_id, kind, status, is_read, created_at FROM notifications WHERE CAST(user_id AS TEXT)=:u"
    if unread_only: q += " AND is_read=0"
    rows = db.execute(text(q + " ORDER BY created_at DESC LIMIT 50"), {"u": str(user_id(user))}).mappings().all()
    items = [{"id": str(r["id"]), "complaint_id": str(r["complaint_id"]), "kind": r["kind"], "status": r["status"],
              "is_read": bool(r["is_read"]), "created_at": iso(r["created_at"])} for r in rows]
    return {"unread": sum(not i["is_read"] for i in items), "items": items}

@router.post("/notifications/read-all")
def read_all(db=Depends(get_db), user=Depends(get_current_user)):
    db.execute(text("UPDATE notifications SET is_read=1 WHERE CAST(user_id AS TEXT)=:u"), {"u": str(user_id(user))})
    db.commit()
    return {"status": "ok"}

@router.post("/notifications/{nid}/read")
def read_one(nid: str, db=Depends(get_db), user=Depends(get_current_user)):
    db.execute(text("UPDATE notifications SET is_read=1 WHERE id=:n AND CAST(user_id AS TEXT)=:u"),
               {"n": nid, "u": str(user_id(user))})
    db.commit()
    return {"status": "ok"}
