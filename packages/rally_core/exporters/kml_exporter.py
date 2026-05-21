"""Export ke format KML 2.2."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from rally_core.routing.models import RouteSegment, RouteWaypoint


KML_NS = "http://www.opengis.net/kml/2.2"
ET.register_namespace("", KML_NS)


def export_kml(
    name: str,
    waypoints: list[RouteWaypoint],
    segments: list[RouteSegment],
) -> str:
    kml = ET.Element(f"{{{KML_NS}}}kml")
    document = ET.SubElement(kml, f"{{{KML_NS}}}Document")
    ET.SubElement(document, f"{{{KML_NS}}}name").text = name

    # Style untuk waypoint
    style = ET.SubElement(document, f"{{{KML_NS}}}Style", attrib={"id": "rally-wp"})
    icon = ET.SubElement(style, f"{{{KML_NS}}}IconStyle")
    icon_url = ET.SubElement(icon, f"{{{KML_NS}}}Icon")
    ET.SubElement(icon_url, f"{{{KML_NS}}}href").text = (
        "https://maps.google.com/mapfiles/kml/paddle/red-circle.png"
    )

    for wp in waypoints:
        placemark = ET.SubElement(document, f"{{{KML_NS}}}Placemark")
        ET.SubElement(placemark, f"{{{KML_NS}}}name").text = wp.name
        ET.SubElement(placemark, f"{{{KML_NS}}}styleUrl").text = "#rally-wp"
        point = ET.SubElement(placemark, f"{{{KML_NS}}}Point")
        ET.SubElement(point, f"{{{KML_NS}}}coordinates").text = (
            f"{wp.coord.lng:.6f},{wp.coord.lat:.6f},0"
        )

    # Garis rute
    line_placemark = ET.SubElement(document, f"{{{KML_NS}}}Placemark")
    ET.SubElement(line_placemark, f"{{{KML_NS}}}name").text = f"{name} Route"
    line_string = ET.SubElement(line_placemark, f"{{{KML_NS}}}LineString")
    ET.SubElement(line_string, f"{{{KML_NS}}}tessellate").text = "1"
    coords: list[str] = []
    for seg in segments:
        for pt in seg.polyline:
            coords.append(f"{pt.lng:.6f},{pt.lat:.6f},0")
    ET.SubElement(line_string, f"{{{KML_NS}}}coordinates").text = " ".join(coords)

    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(kml, encoding="unicode")
