"""Roadbook builder.

Output bisa berupa table dataclass atau markdown render. Field mobile dan
web map UI sama-sama menggunakan struktur RoadbookLeg.
"""

from __future__ import annotations

from rally_core.routing.models import RoadbookLeg, RouteSegment, RouteWaypoint


def build_roadbook_table(
    segments: list[RouteSegment],
    waypoints_by_id: dict[str, RouteWaypoint],
    rally_start_clock_minutes: int | None = None,
    speed_targets: dict[str, float] | None = None,
) -> list[RoadbookLeg]:
    speed_targets = speed_targets or {}
    legs: list[RoadbookLeg] = []
    cum_distance = 0
    cum_duration = 0
    for idx, seg in enumerate(segments, start=1):
        cum_distance += seg.distance_m
        cum_duration += seg.duration_s
        to_wp = waypoints_by_id.get(seg.to_waypoint)
        sub_id = (to_wp.id.rsplit("-", 1)[0] if to_wp else seg.to_waypoint)
        instruction = " | ".join(t.text for t in seg.turn_instructions) or "Lanjutkan"
        eta_clock = None
        if rally_start_clock_minutes is not None:
            total_minutes = rally_start_clock_minutes + cum_duration // 60
            total_minutes = total_minutes % (24 * 60)
            eta_clock = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
        legs.append(
            RoadbookLeg(
                order=idx,
                sub_trayek_id=sub_id,
                from_waypoint=seg.from_waypoint,
                to_waypoint=seg.to_waypoint,
                distance_m=seg.distance_m,
                duration_s=seg.duration_s,
                cumulative_distance_m=cum_distance,
                cumulative_duration_s=cum_duration,
                instruction=instruction,
                landmark=(to_wp.name if to_wp else None),
                eta_clock=eta_clock,
                speed_target_kmh=speed_targets.get(seg.to_waypoint),
                status="verified" if seg.status == "ok" else seg.status,
            )
        )
    return legs


def render_roadbook_markdown(name: str, legs: list[RoadbookLeg]) -> str:
    rows = [
        "| # | Sub | Dari | Ke | Jarak (m) | Durasi (s) | Kum. Jarak | Kum. Waktu | ETA | Instruksi | Status |",
        "|---|----|------|----|-----------|-----------|-----------|-----------|------|-----------|--------|",
    ]
    for leg in legs:
        rows.append(
            "| {order} | {sub} | {fr} | {to} | {dm} | {ds} | {cm} | {cs} | {eta} | {ins} | {st} |".format(
                order=leg.order,
                sub=leg.sub_trayek_id,
                fr=leg.from_waypoint,
                to=leg.to_waypoint,
                dm=leg.distance_m,
                ds=leg.duration_s,
                cm=leg.cumulative_distance_m,
                cs=leg.cumulative_duration_s,
                eta=leg.eta_clock or "-",
                ins=leg.instruction,
                st=leg.status,
            )
        )
    body = "\n".join(rows)
    return f"# Roadbook: {name}\n\n{body}\n"
