"""Optional Sentry initialization.

Sentry SDK adalah optional dependency. Kalau modul belum terinstal, fungsi
``init_sentry`` no-op sehingga test/dev tidak terganggu.

Untuk mengaktifkan: `pip install sentry-sdk` dan set env SENTRY_DSN.
"""

from __future__ import annotations

from app.settings import get_settings


def init_sentry() -> bool:
    settings = get_settings()
    if not settings.sentry_dsn:
        return False
    try:
        import sentry_sdk  # type: ignore[import-not-found]
        from sentry_sdk.integrations.fastapi import FastApiIntegration  # type: ignore[import-not-found]
        from sentry_sdk.integrations.starlette import StarletteIntegration  # type: ignore[import-not-found]
    except Exception:  # noqa: BLE001
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
        release=f"time-rally-api@{settings.app_env}",
    )
    return True
