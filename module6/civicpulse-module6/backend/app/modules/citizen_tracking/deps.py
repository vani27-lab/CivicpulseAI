"""Adapter to Module 1. Override paths via env if Module 1 names differ."""
import importlib, os

def _load(path):
    mod, name = path.rsplit(":", 1)
    return getattr(importlib.import_module(mod), name)

get_db = _load(os.getenv("M1_GET_DB", "app.database:get_db"))
get_current_user = _load(os.getenv("M1_GET_CURRENT_USER", "app.auth:get_current_user"))

def user_id(user):
    return str(user["id"] if isinstance(user, dict) else user.id)
