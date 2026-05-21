"""Export ke format GPX 1.1."""

from __future__ import annotations

from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from rally_core.routing.models import RouteSegment, RouteWaypoint


GPX_NS = "http://www.topografix.com/GPX/1/1"


def export_gpx(
    name: str,
    waypoints: list[RouteWaypoint],
    segments: list[RouteSegment],
    creator: str = "TimeRallyNavigator/0.1",
) -> str:
    gpx = ET.Element(
        "gpx",
        attrib={
            "xmlns": GPX_NS,
            "version": "1.1",
            "creator": creator,
        },
    )
    metadata = ET.SubElement(gpx, "metadata")
    ET.SubElement(metadata, "name").text = name
    ET.SubElement(metadata, "time").text = datetime.now(timezone.utc).isoformat()

    for wp in waypoints:
        wpt = ET.SubElement(
            gpx,
            "wpt",
            attrib={"lat": f"{wp.coord.lat:.6f}", "lon": f"{wp.coord.lng:.6f}"},
        )
        ET.SubElement(wpt, "name").text = wp.name
        ET.SubElement(wpt, "sym").text = wp.role

    trk = ET.SubElement(gpx, "trk")
    ET.SubElement(trk, "name").text = name
    trkseg = ET.SubElement(trk, "trkseg")
    for seg in segments:
        for pt in seg.polyline:
            ET.SubElement(
                trkseg,
                "trkpt",
                attrib={"lat": f"{pt.lat:.6f}", "lon": f"{pt.lng:.6f}"},
            )

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(gpx, encoding="unicode")
