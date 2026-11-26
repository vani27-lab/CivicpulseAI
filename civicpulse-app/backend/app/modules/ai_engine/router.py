"""POST /ai/classify. Mount with app.include_router(build_router(...))."""
from typing import Callable, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from .schemas import ClassificationResult
from .service import ComplaintClassifier, get_default_classifier


def build_router(classifier_provider: Optional[Callable[[], ComplaintClassifier]] = None,
                 auth_dependency: Optional[Callable] = None) -> APIRouter:
    """auth_dependency: pass Module 1's JWT dependency (e.g. get_current_user) to protect the route."""
    provider = classifier_provider or get_default_classifier
    deps = [Depends(auth_dependency)] if auth_dependency else []
    router = APIRouter(prefix="/ai", tags=["ai"], dependencies=deps)

    @router.post("/classify", response_model=ClassificationResult)
    def classify(image: UploadFile = File(...), description: str = Form(""),
                 language: Optional[str] = Form(None),
                 classifier: ComplaintClassifier = Depends(provider)) -> ClassificationResult:
        limit = classifier.settings.max_image_bytes
        data = image.file.read(limit + 1)
        if len(data) > limit:
            raise HTTPException(status_code=413, detail=f"Image exceeds {limit} bytes")
        return classifier.classify_complaint(data, description, language)

    return router
