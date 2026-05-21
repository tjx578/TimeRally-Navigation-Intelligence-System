"""Export RallyEvent ke YAML/EAML.

Format YAML mengikuti gaya knowledge_engine.kmpal + roadbook agar bisa
dikonsumsi UI dan field mobile tanpa transformasi tambahan.
"""

from __future__ import annotations

from typing import Any

import yaml

from rally_core.parser.models import RallyEvent


def event_to_dict(event: RallyEvent) -> dict[str, Any]:
    return {
        "event": {
            "name": event.event_name,
            "trayek": event.trayek_name,
            "location": event.location,
            "rally_start_time": event.rally_start_time,
            "total_distance_km": event.total_distance_km,
            "total_time_minutes": event.total_time_minutes,
        },
        "sub_trayeks": [
            {
                "id": s.id,
                "label": s.label,
                "title": s.title,
                "distance_km": s.distance_km,
                "duration_minutes": s.duration_minutes,
                "speed_mode": s.speed_mode,
                "distance_counted_in_total": s.distance_counted_in_total,
                "waypoints": [
                    {
                        "id": wp.id,
                        "order": wp.order,
                        "raw_text": wp.raw_text,
                        "action": wp.action,
                        "landmark_type": wp.landmark_type,
                        "landmark_name": wp.landmark_name,
                        "relation": wp.relation,
                        "kmpal_marker": wp.kmpal_marker,
                        "notes": wp.notes,
                        "ambiguous": wp.ambiguous,
                    }
                    for wp in s.waypoints
                ],
            }
            for s in event.sub_trayeks
        ],
    }


def export_event_yaml(event: RallyEvent) -> str:
    return yaml.safe_dump(event_to_dict(event), allow_unicode=True, sort_keys=False)
