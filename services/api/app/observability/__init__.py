"""Observability bootstrap (Sentry optional)."""

from app.observability.sentry import init_sentry

__all__ = ["init_sentry"]
