"""Health/readiness endpoints for orchestration and monitoring."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.settings import get_settings


router = APIRouter()


@router.get("/health")
@router.get("/healthz")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "api",
        "app_env": settings.app_env,
        "routing_default_provider": settings.routing_default_provider,
        "routing_provider_priority": [
            settings.routing_provider_primary,
            settings.routing_provider_fallback,
            settings.routing_provider_standby,
        ],
        "google_enabled": settings.google_enabled,
        "ocr_worker_configured": bool(settings.ocr_worker_url),
    }


@router.get("/readyz")
def ready() -> dict:
    settings = get_settings()
    exports_root = Path(settings.exports_root)
    knowledge_root = Path(settings.knowledge_root)
    checks = {
        "cors_configured": bool(settings.cors_origins),
        "routing_gateway_url": settings.routing_gateway_url,
        "exports_root_parent_exists": exports_root.parent.exists(),
        "exports_root_gcs": settings.exports_root.startswith("gs://"),
        "knowledge_root_exists": knowledge_root.exists(),
        "ocr_worker_url_configured": bool(settings.ocr_worker_url),
    }
    exports_ready = checks["exports_root_gcs"] or checks["exports_root_parent_exists"]
    status = "ready" if checks["cors_configured"] and exports_ready else "degraded"
    return {"status": status, "service": "api", "checks": checks}
