"""Standalone dev app for Module 3. In the real project, include the router in Module 1's app."""
from fastapi import FastAPI

from .modules.ai_engine.router import build_router

app = FastAPI(title="CivicPulse AI - Module 3 (AI Engine)")
app.include_router(build_router())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "module": "ai_engine"}
