import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings


os.makedirs(settings.upload_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    description="Civic issue reporting and resolution. Modules 1-2: foundation and citizen reporting.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Saved photographs are served at /uploads/... (the website shows them in Modules 5 and 6).
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}
