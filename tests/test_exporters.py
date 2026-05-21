from rally_core.exporters import (
    export_event_yaml,
    export_geojson,
    export_gpx,
    export_kml,
    render_roadbook_markdown,
    build_roadbook_table,
)
from rally_core.parser.models import ParsedWaypoint, RallyEvent, SubTrayek
from rally_core.routing.models import (
    LatLng,
    RouteSegment,
    RouteWaypoint,
    TurnInstruction,
)


def _sample_event() -> RallyEvent:
    return RallyEvent(
        event_name="Bali Demo",
        total_distance_km=10.0,
        total_time_minutes=30,
        sub_trayeks=[
            SubTrayek(
                id="sub-a",
                label="A",
                title="Start",
                distance_km=5.0,
                duration_minutes=15,
                speed_mode="average_speed",
                waypoints=[
                    ParsedWaypoint(id="sub-a-WP001", sub_trayek_id="sub-a", order=1, raw_text="BKR di POM"),
                ],
            )
        ],
    )


def _sample_route() -> tuple[list[RouteWaypoint], list[RouteSegment]]:
    wps = [
        RouteWaypoint(id="w1", name="Start", coord=LatLng(-8.67, 115.22), role="start"),
        RouteWaypoint(id="w2", name="Finish", coord=LatLng(-8.68, 115.23), role="finish"),
    ]
    segments = [
        RouteSegment(
            from_waypoint="w1",
            to_waypoint="w2",
            distance_m=1234,
            duration_s=200,
            polyline=[wps[0].coord, wps[1].coord],
            turn_instructions=[TurnInstruction(text="JT", distance_m=1000, type="continue")],
        )
    ]
    return wps, segments


def test_export_yaml_contains_event_name():
    out = export_event_yaml(_sample_event())
    assert "Bali Demo" in out
    assert "sub_trayeks:" in out


def test_export_gpx_has_trkpt():
    wps, segs = _sample_route()
    out = export_gpx("demo", wps, segs)
    assert "<wpt" in out
    assert "<trkpt" in out


def test_export_kml_has_placemark():
    wps, segs = _sample_route()
    out = export_kml("demo", wps, segs)
    assert "<Placemark" in out
    assert "LineString" in out


def test_export_geojson_features():
    wps, segs = _sample_route()
    out = export_geojson(wps, segs)
    assert "FeatureCollection" in out
    assert "LineString" in out


def test_roadbook_markdown_table():
    wps, segs = _sample_route()
    legs = build_roadbook_table(segs, {wp.id: wp for wp in wps}, rally_start_clock_minutes=7 * 60 + 30)
    md = render_roadbook_markdown("demo", legs)
    assert "| 1 |" in md
    assert "Roadbook: demo" in md
