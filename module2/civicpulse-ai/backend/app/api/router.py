"""All API routes are collected here. Later modules add their router in this file."""
from fastapi import APIRouter

from app.api.routes import auth, departments, health, reports, users

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(reports.router)  # Module 2

# Module 3 -> AI router goes here
# Module 4 -> (mostly internal services, little or no new routes)
# Module 5 -> officer dashboard router goes here
# Module 6 -> citizen tracking router goes here
