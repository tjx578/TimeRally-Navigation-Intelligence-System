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
    routing_default_provider: str = "valhalla"
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


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL"),
        routing_default_provider=os.getenv("ROUTING_DEFAULT_PROVIDER", "valhalla"),
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
    )
