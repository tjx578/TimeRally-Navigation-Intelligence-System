"""Settings API service - dibaca dari environment.

Catatan: kita pakai `os.environ` langsung agar tidak perlu menambah dependensi
pydantic-settings. Caller bisa membungkus dengan `lru_cache` jika perlu.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_env: str = "development"
    database_url: str | None = None
    redis_url: str | None = None
    routing_default_provider: str = "auto"
    routing_provider_primary: str = "osrm"
    routing_provider_fallback: str = "valhalla"
    routing_provider_standby: str = "graphhopper"
    routing_allow_mock_fallback: bool = True
    routing_gateway_url: str = "http://routing-gateway:8010"
    valhalla_url: str = "http://localhost:8002"
    osrm_url: str = "http://localhost:5000"
    graphhopper_url: str = "http://localhost:8989"
    nominatim_url: str = "http://localhost:8080"
    tileserver_url: str = "http://localhost:8081"
    traccar_url: str = "http://localhost:8082"
    google_maps_api_key: str | None = None
    google_enabled: bool = False
    data_root: str = "data"
    exports_root: str = "exports"
    knowledge_root: str = "data/curated"
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_csv_tuple(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL"),
        routing_default_provider=os.getenv("ROUTING_DEFAULT_PROVIDER", "auto"),
        routing_provider_primary=os.getenv("ROUTING_PROVIDER_PRIMARY", "osrm"),
        routing_provider_fallback=os.getenv("ROUTING_PROVIDER_FALLBACK", "valhalla"),
        routing_provider_standby=os.getenv("ROUTING_PROVIDER_STANDBY", "graphhopper"),
        routing_allow_mock_fallback=_to_bool(
            os.getenv("ROUTING_ALLOW_MOCK_FALLBACK"),
            default=os.getenv("APP_ENV", "development").strip().lower() != "production",
        ),
        routing_gateway_url=os.getenv("ROUTING_GATEWAY_URL", "http://routing-gateway:8010"),
        valhalla_url=os.getenv("VALHALLA_URL", "http://localhost:8002"),
        osrm_url=os.getenv("OSRM_URL", "http://localhost:5000"),
        graphhopper_url=os.getenv("GRAPHHOPPER_URL", "http://localhost:8989"),
        nominatim_url=os.getenv("NOMINATIM_URL", "http://localhost:8080"),
        tileserver_url=os.getenv("TILESERVER_URL", "http://localhost:8081"),
        traccar_url=os.getenv("TRACCAR_URL", "http://localhost:8082"),
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY") or None,
        google_enabled=_to_bool(os.getenv("GOOGLE_ENABLED"), default=False),
        data_root=os.getenv("DATA_ROOT", "data"),
        exports_root=os.getenv("EXPORTS_ROOT", "exports"),
        knowledge_root=os.getenv("KNOWLEDGE_ROOT", "data/curated"),
        cors_origins=_to_csv_tuple(
            os.getenv("API_CORS_ORIGINS"),
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        ),
    )
