"""Smoke test API menggunakan TestClient FastAPI."""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
except Exception as exc:  # pragma: no cover
    client = None
    pytestmark = pytest.mark.skip(reason=f"FastAPI test client tidak siap: {exc}")


def test_health_endpoint():
    assert client is not None
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_healthz_and_readyz_endpoints():
    assert client is not None
    health = client.get("/healthz")
    ready = client.get("/readyz")
    assert health.status_code == 200
    assert ready.status_code == 200
    assert health.json()["service"] == "api"
    assert ready.json()["status"] in {"ready", "degraded"}


def test_parse_endpoint_minimal():
    assert client is not None
    resp = client.post(
        "/v1/rally/parse",
        json={"raw_text": "Sub A: dummy\nMode: Average Speed\nJarak: 10 km\nWaktu: 30 menit\nJT di O Lapangan"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sub_trayek_count"] >= 1
    assert body["waypoint_count"] >= 1


def test_parse_endpoint_exposes_start_finish_state():
    assert client is not None
    resp = client.post(
        "/v1/rally/parse",
        json={
            "raw_text": (
                "Sub 1.1:\n"
                "START - BKR - BR Anyar Tembles, dengan jarak, 15,8km\n\n"
                "Sub 1.2:\n"
                "BKR - Jalan Rama - Finish di Kantor Desa Pergung, jarak 4,2km"
            )
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    sub_11, sub_12 = body["sub_trayeks"]
    assert sub_11["label"] == "1.1"
    assert sub_11["start_status"] == "missing_location"
    assert sub_11["needs_user_start"] is True
    assert sub_11["finish_status"] == "inferred_last_waypoint"
    assert sub_11["finish_raw_text"] == "BR Anyar Tembles"
    assert sub_12["start_status"] == "inherited"
    assert sub_12["start_raw_text"] == "BR Anyar Tembles"
    assert sub_12["finish_status"] == "explicit"


def test_photo_ocr_without_worker_falls_back_to_manual():
    assert client is not None
    resp = client.post(
        "/v1/rally/photo-ocr",
        json={
            "photos": [
                {
                    "filename": "soal.jpg",
                    "mime_type": "image/jpeg",
                    "image_base64": "dGVzdA==",
                }
            ]
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ocr_worker_unavailable_manual_parse_required"
    assert body["photo_count"] == 1
    assert "OCR worker belum dikonfigurasi" in " ".join(body["warnings"])


def test_validation_route_endpoint():
    assert client is not None
    resp = client.post(
        "/v1/validation/route",
        json={
            "target_distance_km": 10.0,
            "target_time_minutes": 30,
            "calculated_distance_km": 10.1,
            "calculated_time_minutes": 30.2,
            "chaining_gap_meters": 12,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["distance_status"] in {"compliant", "warning", "violation", "unchecked"}


def test_routing_endpoint_mock():
    assert client is not None
    resp = client.post(
        "/v1/routing/route",
        json={
            "provider": "mock",
            "profile": "rally_car",
            "allow_reorder": False,
            "waypoints": [
                {"id": "w1", "name": "Start", "coordinate": {"lat": -8.67, "lng": 115.22}},
                {"id": "w2", "name": "Finish", "coordinate": {"lat": -8.68, "lng": 115.23}},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_distance_m"] > 0


def test_routing_endpoint_rounds_fractional_provider_values(monkeypatch):
    assert client is not None
    import app.routers.routing as routing_router
    from rally_core.routing.models import ProviderResult, RouteSegment

    def fake_route_event(*args, **kwargs):
        return ProviderResult(
            provider="osrm",
            segments=[
                RouteSegment(
                    from_waypoint="wp-denpasar",
                    to_waypoint="wp-gianyar",
                    distance_m=28683.4,  # type: ignore[arg-type]
                    duration_s=1622.6,  # type: ignore[arg-type]
                    provider="osrm",
                    status="ok",
                )
            ],
            total_distance_m=28683.4,  # type: ignore[arg-type]
            total_duration_s=1622.6,  # type: ignore[arg-type]
        )

    monkeypatch.setattr(routing_router, "route_event", fake_route_event)

    resp = client.post(
        "/v1/routing/route",
        json={
            "provider": "osrm",
            "waypoints": [
                {"id": "wp-denpasar", "name": "Denpasar", "coordinate": {"lat": -8.6705, "lng": 115.2126}},
                {"id": "wp-gianyar", "name": "Gianyar", "coordinate": {"lat": -8.5442, "lng": 115.3250}},
            ],
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["legs"][0]["distance_m"] == 28683
    assert body["legs"][0]["duration_s"] == 1623
    assert body["total_distance_m"] == 28683
    assert body["total_duration_s"] == 1623


def test_export_endpoint_returns_artifacts():
    assert client is not None
    resp = client.post(
        "/v1/export/artifacts",
        json={
            "event_id": "evt-1",
            "event_name": "Demo Event",
            "formats": ["yaml", "gpx", "kml"],
            "waypoints": [
                {"id": "w1", "name": "Start", "coordinate": {"lat": -8.67, "lng": 115.22}},
                {"id": "w2", "name": "Finish", "coordinate": {"lat": -8.68, "lng": 115.23}},
            ],
            "segments": [
                {
                    "from_waypoint": "w1",
                    "to_waypoint": "w2",
                    "distance_m": 1200,
                    "duration_s": 180,
                    "polyline": [
                        {"lat": -8.67, "lng": 115.22},
                        {"lat": -8.68, "lng": 115.23},
                    ],
                }
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["artifacts"]) == 3
    assert all(a["status"] == "generated" for a in body["artifacts"])
