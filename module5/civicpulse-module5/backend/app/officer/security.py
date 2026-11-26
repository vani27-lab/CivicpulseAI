"""Role-based access control for officer-only routes.

Authentication (JWT parsing, 401s) stays in Module 1's ``get_current_user``;
this file only adds the role gate on top. Citizens always receive 403."""
from fastapi import Depends, HTTPException

from . import integration
from .config import get_settings


def require_roles(*roles: str):
    allowed = {r.lower() for r in roles}

    def dependency(user=Depends(integration.get_current_user)):
        if integration.user_role(user) not in allowed:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "This area is for authorised officers only."},
            )
        return user

    return dependency


def require_officer(user=Depends(integration.get_current_user)):
    if integration.user_role(user) not in get_settings().officer_roles:
        raise HTTPException(
            status_code=403,
            detail={"code": "forbidden", "message": "This area is for authorised officers only."},
        )
    return user


def is_admin(user) -> bool:
    return integration.user_role(user) == get_settings().admin_role
