"""Pure helpers: shape DB rows into citizen-safe payloads (no officer data)."""
def norm(s):
    return (s or "").strip().lower().replace(" ", "_").replace("-", "_")

def iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v

def public_history(rows):
    out = []
    for r in rows:
        new = norm(r["new_status"])
        out.append({
            "id": str(r["id"]), "old_status": norm(r["old_status"]) or None,
            "new_status": new, "comment": r["comment"],
            # after-photo only ever surfaces on resolution entries
            "after_photo_url": r["after_photo_url"] if new == "resolved" else None,
            "created_at": iso(r["created_at"]),
        })
    return out

def compute_stats(statuses):
    s = [norm(x) for x in statuses]
    return {"total": len(s),
            "pending": sum(x in ("submitted", "assigned") for x in s),
            "in_progress": sum(x == "in_progress" for x in s),
            "resolved": sum(x == "resolved" for x in s)}
