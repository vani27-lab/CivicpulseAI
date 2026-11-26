"""The ONLY place Module 5 touches Module 1 internals.

Module 1 is not available while this module is built, so its DB-session and
auth dependencies are resolved from environment variables of the form
``dotted.module:attribute`` at import time:

    M5_GET_DB            default  app.db.session:get_db
    M5_GET_CURRENT_USER  default  app.core.security:get_current_user

``get_current_user`` must raise 401 for a missing/invalid JWT and return an
object (or dict) exposing ``id``, ``name`` and ``role``. If Module 1 uses other
names, change the two env vars - no code edits needed.
"""
import importlib
import os


def _resolve(env_name: str, default: str):
    target = os.getenv(env_name, default)
    module_name, _, attr = target.partition(":")
    try:
        return getattr(importlib.import_module(module_name), attr)
    except (ImportError, AttributeError) as exc:
        raise ImportError(
            f"Module 5 could not resolve {env_name}='{target}'. Point it at the Module 1 "
            f"dependency (format 'package.module:callable'). Original error: {exc}"
        ) from exc


get_db = _resolve("M5_GET_DB", "app.db.session:get_db")
get_current_user = _resolve("M5_GET_CURRENT_USER", "app.core.security:get_current_user")


def _field(user, name, default=None):
    if isinstance(user, dict):
        return user.get(name, default)
    return getattr(user, name, default)


def user_id(user):
    return _field(user, "id")


def user_name(user):
    return _field(user, "name")


def user_role(user) -> str:
    role = _field(user, "role", "")
    role = getattr(role, "value", role)
    return str(role or "").strip().lower()
