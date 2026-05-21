"""Parser per sub-trayek.

Sub-trayek dalam soal NaviPRO biasanya berisi header dengan jarak, waktu, mode
kecepatan, kemudian list waypoint baris-per-baris.
"""

from __future__ import annotations

import re
from typing import Optional

from rally_core.parser.models import ParsedWaypoint, SpeedMode, SubTrayek
from rally_core.parser.tokenizer import WaypointToken, tokenize_waypoint


_SUB_DISTANCE_RE = re.compile(r"(\d+(?:[\.,]\d+)?)\s*km(?!\s*/?\s*jam)", re.IGNORECASE)
_EXPLICIT_DISTANCE_RE = re.compile(
    r"(?im)(?:jarak|distance|sejauh)\s*(?:[:=\-]\s*)?\*{0,2}\s*(\d+(?:[\.,]\d+)?)\s*km(?!\s*/?\s*jam)"
)
_DISTANCE_UNDEFINED_RE = re.compile(
    r"(?im)jarak\s*(?:[:=\-]\s*)?\*{0,2}\s*(?:tidak\s+ditentukan|n/?a|berbasis\s+waktu)"
)
_SUB_DURATION_RE = re.compile(r"(\d{1,3}(?:[\.,]\d+)?)\s*(?:menit|min|m)\b", re.IGNORECASE)
_EXPLICIT_DURATION_RE = re.compile(
    r"(?im)(?:waktu|durasi|selama|time)\s*(?:[:=\-]\s*)?\*{0,2}\s*(\d{1,3}(?:[\.,]\d+)?)\s*(?:menit|min|m)\b"
)
_SUB_TITLE_RE = re.compile(r"(?im)^title\s*[:\-]\s*(.+)$")
_SUB_MODE_RE = re.compile(r"(?im)^(?:[*\-\s]*\*{0,2})?(?:mode|mode\s+kecepatan|kecepatan)\s*[:\-]\s*(.+)$")
_FIRST_LINE_TITLE = re.compile(r"^(.*?)(?=$|\.)")
_WAYPOINT_PREFIX_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\d+[\.)]\s*)?")


def _detect_speed_mode(text: str) -> SpeedMode:
    mode_match = _SUB_MODE_RE.search(text)
    if mode_match:
        text = mode_match.group(1)
    upper = text.upper()
    if "KEC TETAP DETIK" in upper or "TETAP DETIK" in upper or "FIXED SEC" in upper:
        return "fixed_second"
    if "KEC TETAP MENIT" in upper or "TETAP MENIT" in upper or "FIXED MIN" in upper:
        return "fixed_minute"
    if "SISA JARAK" in upper or "REMAINING" in upper:
        return "remaining_distance"
    if "KEC RATA" in upper or "RATA-RATA" in upper or "AVERAGE" in upper:
        return "average_speed"
    if "ZERO TRIP" in upper or "LIAISON" in upper:
        return "liaison_zero_trip"
    if "SANTAI" in upper or "BEBAS" in upper:
        return "free_time"
    return "unknown"


def _clean_metadata_line(line: str) -> str:
    return line.strip().strip("-* ").replace("**", "").strip()


def _clean_waypoint_line(line: str) -> str:
    return _WAYPOINT_PREFIX_RE.sub("", line).strip()


def _build_waypoint(
    sub_trayek_id: str,
    order: int,
    line: str,
) -> Optional[ParsedWaypoint]:
    tokens: list[WaypointToken] = tokenize_waypoint(line)
    if not tokens:
        return None
    wp = ParsedWaypoint(
        id=f"{sub_trayek_id}-WP{order:03d}",
        sub_trayek_id=sub_trayek_id,
        order=order,
        raw_text=line.strip(),
    )

    name_parts: list[str] = []
    seen_action = False
    seen_landmark = False
    for tok in tokens:
        if tok.kind == "action" and not seen_action:
            wp.action = tok.value
            seen_action = True
        elif tok.kind == "landmark_type":
            if not seen_landmark:
                wp.landmark_type = tok.value
                seen_landmark = True
            else:
                # Landmark sekunder (mis. T (simpang tiga) br (banjar)) di-gabungkan
                # supaya informasi tidak hilang.
                wp.landmark_type = f"{wp.landmark_type}_{tok.value}"
                wp.notes.append(f"secondary_landmark:{tok.value}")
        elif tok.kind == "landmark_modifier":
            if wp.landmark_type:
                wp.landmark_type = f"{wp.landmark_type}_{tok.value}"
            else:
                wp.notes.append(f"modifier_only:{tok.value}")
        elif tok.kind == "relation":
            wp.relation = tok.value
        elif tok.kind == "kmpal":
            wp.kmpal_marker = tok.value
        elif tok.kind == "direction":
            wp.notes.append(f"direction:{tok.value}")
        elif tok.kind == "name":
            name_parts.append(tok.text)
        elif tok.kind == "number":
            name_parts.append(tok.text)
    landmark_name = " ".join(name_parts).strip()
    wp.landmark_name = landmark_name or None

    if not (wp.action or wp.landmark_type or wp.landmark_name or wp.kmpal_marker):
        wp.ambiguous = True
        wp.notes.append("no_recognizable_token")
    return wp


def parse_sub_trayek_block(label: str, body: str, order: int) -> SubTrayek:
    sub_id = f"sub-{label.lower()}"
    sub = SubTrayek(id=sub_id, label=label, title="", raw_lines=body.splitlines())

    title_match = _SUB_TITLE_RE.search(body)
    if title_match:
        sub.title = title_match.group(1).strip()

    dist_match = _EXPLICIT_DISTANCE_RE.search(body) or _SUB_DISTANCE_RE.search(body)
    if _DISTANCE_UNDEFINED_RE.search(body):
        sub.distance_km = None
        sub.distance_counted_in_total = False
    elif dist_match:
        sub.distance_km = float(dist_match.group(1).replace(",", "."))

    dur_match = _EXPLICIT_DURATION_RE.search(body) or _SUB_DURATION_RE.search(body)
    if dur_match:
        sub.duration_minutes = float(dur_match.group(1).replace(",", "."))

    sub.speed_mode = _detect_speed_mode(body)
    if sub.speed_mode == "liaison_zero_trip" or sub.distance_km is None:
        sub.distance_counted_in_total = False

    if not sub.title:
        # Title fallback: ambil baris pertama yang bukan header metadata.
        for raw in body.splitlines():
            line = _clean_metadata_line(raw)
            if not line:
                continue
            if _SUB_DISTANCE_RE.search(line) and len(line) < 40:
                continue
            if _SUB_DURATION_RE.search(line) and len(line) < 40:
                continue
            sub.title = line[:160]
            break

    # Parse waypoint lines: skip baris metadata (dist/dur/speed mode/title).
    wp_order = 0
    for raw in body.splitlines():
        line = _clean_metadata_line(raw)
        if not line:
            continue
        if _SUB_DISTANCE_RE.fullmatch(line):
            continue
        if _SUB_DURATION_RE.fullmatch(line):
            continue
        if line.lower().startswith(
            ("title", "jarak", "waktu", "durasi", "mode", "mode kecepatan", "kecepatan", "titik navigasi")
        ):
            continue
        line = _clean_waypoint_line(line)
        if not line:
            continue
        wp_order += 1
        wp = _build_waypoint(sub_id, wp_order, line)
        if wp:
            sub.waypoints.append(wp)
    return sub
