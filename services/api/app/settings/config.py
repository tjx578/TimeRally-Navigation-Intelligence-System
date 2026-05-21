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
    # Public URL (untuk Sentry tag dan signed-URL builder).
    public_web_url: str | None = None
    public_api_url: str | None = None
    # Supabase (server-side only; service_role_key tidak boleh bocor ke client).
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_db_url: str | None = None
    supabase_exports_bucket: str = "exports-private"
    supabase_uploads_bucket: str = "uploads-private"
    # Google Cloud Storage mode. When EXPORTS_ROOT starts with gs:// this bucket
    # is inferred automatically, but explicit values help scripts and readiness.
    gcs_bucket_name: str | None = None
    gcs_exports_prefix: str = "exports"
    gcs_photos_prefix: str = "photos"
    # Observability.
    sentry_dsn: str | None = None
    sentry_environment: str = "development"
    sentry_traces_sample_rate: float = 0.0
    # TTL signed URL untuk artefak export private (detik).
    export_signed_url_ttl_seconds: int = 900


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_csv_tuple(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _to_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _to_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development")
    return Settings(
        app_env=app_env,
        database_url=os.getenv("DATABASE_URL"),
        redis_url=os.getenv("REDIS_URL"),
        routing_default_provider=os.getenv("ROUTING_DEFAULT_PROVIDER", "auto"),
        routing_provider_primary=os.getenv("ROUTING_PROVIDER_PRIMARY", "osrm"),
        routing_provider_fallback=os.getenv("ROUTING_PROVIDER_FALLBACK", "valhalla"),
        routing_provider_standby=os.getenv("ROUTING_PROVIDER_STANDBY", "graphhopper"),
        routing_allow_mock_fallback=_to_bool(
            os.getenv("ROUTING_ALLOW_MOCK_FALLBACK"),
            default=app_env.strip().lower() != "production",
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
        public_web_url=os.getenv("PUBLIC_WEB_URL") or None,
        public_api_url=os.getenv("PUBLIC_API_URL") or None,
        supabase_url=os.getenv("SUPABASE_URL") or None,
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY") or None,
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY") or None,
        supabase_db_url=os.getenv("SUPABASE_DB_URL") or None,
        supabase_exports_bucket=os.getenv("SUPABASE_EXPORTS_BUCKET", "exports-private"),
        supabase_uploads_bucket=os.getenv("SUPABASE_UPLOADS_BUCKET", "uploads-private"),
        gcs_bucket_name=os.getenv("GCS_BUCKET_NAME") or None,
        gcs_exports_prefix=os.getenv("GCS_EXPORTS_PREFIX", "exports").strip("/"),
        gcs_photos_prefix=os.getenv("GCS_PHOTOS_PREFIX", "photos").strip("/"),
        sentry_dsn=os.getenv("SENTRY_DSN") or None,
        sentry_environment=os.getenv("SENTRY_ENVIRONMENT", app_env),
        sentry_traces_sample_rate=_to_float(os.getenv("SENTRY_TRACES_SAMPLE_RATE"), 0.0),
        export_signed_url_ttl_seconds=_to_int(os.getenv("EXPORT_SIGNED_URL_TTL_SECONDS"), 900),
    )
