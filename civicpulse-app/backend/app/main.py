import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings
from app.officer import include_module5_routers
from app.modules.citizen_tracking.router import router as citizen_tracking_router

os.makedirs(settings.upload_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    description="Civic issue reporting and resolution. Unified Modules 1-6.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Module 6 citizen tracking routes (include before generic complaint routes)
app.include_router(citizen_tracking_router)
app.include_router(citizen_tracking_router, prefix="/api")

# 2. Module 1 & 2 API router
app.include_router(api_router)

# 3. Module 5 Officer dashboard routers
include_module5_routers(app)

# Saved photographs are served at /uploads/... and /media/...
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}
