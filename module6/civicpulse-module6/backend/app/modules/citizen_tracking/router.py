"""Module 6 citizen routes. Mount with app.include_router(router) BEFORE any
generic /complaints/{id} route so /complaints/mine is not shadowed."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from .deps import get_db, get_current_user, user_id
from .shaping import public_history, compute_stats, norm, iso
from .translation import translate_cached

router = APIRouter(tags=["citizen-tracking"])

def _require_owned(db, cid, uid):
    ok = db.execute(text("SELECT 1 FROM reports WHERE complaint_id=:c AND user_id=:u LIMIT 1"),
                    {"c": cid, "u": uid}).first()
    if not ok:  # 404, not 403: don't reveal that other citizens' complaints exist
        raise HTTPException(404, "Complaint not found")

def _history(db, cid):
    rows = db.execute(text("SELECT id, old_status, new_status, comment, after_photo_url, created_at "
                           "FROM status_history WHERE complaint_id=:c ORDER BY created_at"), {"c": cid}).mappings().all()
    return public_history(rows)

@router.get("/complaints/mine")
def mine(db=Depends(get_db), user=Depends(get_current_user)):
    rows = db.execute(text("""
      SELECT c.id, c.issue_type, c.status, c.priority_band, c.created_at,
        (SELECT r.image_url FROM reports r WHERE r.complaint_id=c.id AND r.user_id=:u ORDER BY r.created_at LIMIT 1) AS thumbnail
      FROM complaints c
      WHERE EXISTS (SELECT 1 FROM reports r WHERE r.complaint_id=c.id AND r.user_id=:u)
      ORDER BY c.created_at DESC"""), {"u": user_id(user)}).mappings().all()
    items = [{"id": str(r["id"]), "issue_type": r["issue_type"], "status": norm(r["status"]),
              "priority_band": r["priority_band"], "created_at": iso(r["created_at"]),
              "thumbnail": r["thumbnail"]} for r in rows]
    return {"stats": compute_stats([i["status"] for i in items]), "items": items}

@router.get("/complaints/{cid}")
def detail(cid: str, db=Depends(get_db), user=Depends(get_current_user)):
    uid = user_id(user)
    _require_owned(db, cid, uid)
    c = db.execute(text("SELECT id, issue_type, status, priority_band, created_at, updated_at FROM complaints WHERE id=:c"),
                   {"c": cid}).mappings().first()
    mine_r = db.execute(text("""SELECT image_url, original_description, translated_description, latitude, longitude
                                FROM reports WHERE complaint_id=:c AND user_id=:u ORDER BY created_at LIMIT 1"""),
                        {"c": cid, "u": uid}).mappings().first()
    hist = _history(db, cid)
    after = next((h["after_photo_url"] for h in reversed(hist) if h["after_photo_url"]), None)
    return {"id": str(c["id"]), "issue_type": c["issue_type"], "status": norm(c["status"]),
            "priority_band": c["priority_band"], "created_at": iso(c["created_at"]), "updated_at": iso(c["updated_at"]),
            "before_photo_url": mine_r["image_url"], "after_photo_url": after if norm(c["status"]) == "resolved" else None,
            "original_description": mine_r["original_description"],
            "translated_description": mine_r["translated_description"],
            "latitude": mine_r["latitude"], "longitude": mine_r["longitude"]}

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
    q = "SELECT id, complaint_id, kind, status, is_read, created_at FROM notifications WHERE user_id=:u"
    if unread_only: q += " AND is_read=false"
    rows = db.execute(text(q + " ORDER BY created_at DESC LIMIT 50"), {"u": user_id(user)}).mappings().all()
    items = [{"id": str(r["id"]), "complaint_id": str(r["complaint_id"]), "kind": r["kind"], "status": r["status"],
              "is_read": r["is_read"], "created_at": iso(r["created_at"])} for r in rows]
    return {"unread": sum(not i["is_read"] for i in items), "items": items}

@router.post("/notifications/read-all", status_code=204)
def read_all(db=Depends(get_db), user=Depends(get_current_user)):
    db.execute(text("UPDATE notifications SET is_read=true WHERE user_id=:u"), {"u": user_id(user)}); db.commit()

@router.post("/notifications/{nid}/read", status_code=204)
def read_one(nid: str, db=Depends(get_db), user=Depends(get_current_user)):
    db.execute(text("UPDATE notifications SET is_read=true WHERE id=:n AND user_id=:u"), {"n": nid, "u": user_id(user)}); db.commit()
