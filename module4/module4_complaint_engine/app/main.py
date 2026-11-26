"""Standalone dev app for Module 4 (needs DATABASE_URL with PostGIS + Module 1's tables).

In the real project, don't use this file: include build_router(...) in Module 1's app and pass
Module 1's session dependency, JWT user dependency and officer dependency.
"""
import os
from functools import lru_cache

from fastapi import Depends, FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .modules.complaint_engine.config import Settings
from .modules.complaint_engine.embedder import ClipEmbedder
from .modules.complaint_engine.engine import ComplaintProcessor, default_classifier
from .modules.complaint_engine.places import StaticPlaceProvider
from .modules.complaint_engine.repository_sqlalchemy import SqlAlchemyComplaintRepository
from .modules.complaint_engine.router import build_router

settings = Settings.from_env()
_engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)  # e.g. postgresql+psycopg2://...
_Session = sessionmaker(bind=_engine, expire_on_commit=False)


@lru_cache
def _embedder() -> ClipEmbedder:
    return ClipEmbedder(settings.clip_model_name)


@lru_cache
def _places() -> StaticPlaceProvider:
    return StaticPlaceProvider.from_file(settings.places_path, settings)


def get_processor():
    session: Session = _Session()
    try:
        yield ComplaintProcessor(SqlAlchemyComplaintRepository(session), default_classifier(),
                                 _embedder(), _places(), settings)
    finally:
        session.close()


app = FastAPI(title="CivicPulse AI - Module 4 (Complaint Engine)")
# user_dependency / officer_dependency come from Module 1; without officer_dependency, /split returns 503.
app.include_router(build_router(get_processor))


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "module": "complaint_engine"}
