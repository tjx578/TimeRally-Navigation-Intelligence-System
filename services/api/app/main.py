"""FastAPI entrypoint Time Rally Navigation Intelligence System."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import exports, health, places, probability, rally, routing, validation
from app.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Time Rally Navigation Intelligence System",
        version="0.1.0",
        summary="Local-first rally intelligence backend.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(rally.router, prefix="/v1/rally", tags=["rally"])
    app.include_router(places.router, prefix="/v1/places", tags=["places"])
    app.include_router(routing.router, prefix="/v1/routing", tags=["routing"])
    app.include_router(validation.router, prefix="/v1/validation", tags=["validation"])
    app.include_router(exports.router, prefix="/v1/export", tags=["export"])
    app.include_router(probability.router, prefix="/v1/probability", tags=["probability"])

    @app.get("/")
    def root() -> dict:
        return {
            "name": "Time Rally Navigation Intelligence System",
            "version": "0.1.0",
            "docs": "/docs",
            "endpoints": [
                "/v1/rally/parse",
                "/v1/rally/photo-ocr",
                "/v1/places/search",
                "/v1/routing/route",
                "/v1/validation/route",
                "/v1/validation/timing-table",
                "/v1/probability/infer-missing-waypoint",
                "/v1/probability/route-edit",
                "/v1/export/artifacts",
            ],
        }

    return app


app = create_app()
