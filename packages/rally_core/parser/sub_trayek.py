"""Parser per sub-trayek.

Sub-trayek dalam soal NaviPRO biasanya berisi header dengan jarak, waktu, mode
kecepatan, kemudian list waypoint baris-per-baris.
"""

from __future__ import annotations

import re
from typing import Optional

from rally_core.parser.models import ParsedWaypoint, SpeedMode, SubTrayek
from rally_core.parser.tokenizer import WaypointToken, tokenize_waypoint


_SUB_DISTANCE_RE = re.compile(r"(\d+(?:[\.,]\d+)?)\s*km", re.IGNORECASE)
_SUB_DURATION_RE = re.compile(r"(\d{1,3})\s*(?:menit|min|m)\b", re.IGNORECASE)
_SUB_TITLE_RE = re.compile(r"(?im)^title\s*[:\-]\s*(.+)$")
_FIRST_LINE_TITLE = re.compile(r"^(.*?)(?=$|\.)")


def _detect_speed_mode(text: str) -> SpeedMode:
    upper = text.upper()
    if "ZERO TRIP" in upper or "LIAISON" in upper:
        return "liaison_zero_trip"
    if "KEC TETAP DETIK" in upper or "TETAP DETIK" in upper or "FIXED SEC" in upper:
        return "fixed_second"
    if "SISA JARAK" in upper or "REMAINING" in upper:
        return "remaining_distance"
    if "KEC RATA" in upper or "RATA-RATA" in upper or "AVERAGE" in upper:
        return "average_speed"
    return "unknown"


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

    dist_match = _SUB_DISTANCE_RE.search(body)
    if dist_match:
        sub.distance_km = float(dist_match.group(1).replace(",", "."))

    dur_match = _SUB_DURATION_RE.search(body)
    if dur_match:
        sub.duration_minutes = float(dur_match.group(1))

    sub.speed_mode = _detect_speed_mode(body)
    if sub.speed_mode == "liaison_zero_trip":
        sub.distance_counted_in_total = False

    if not sub.title:
        # Title fallback: ambil baris pertama yang bukan header metadata.
        for raw in body.splitlines():
            line = raw.strip()
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
        line = raw.strip()
        if not line:
            continue
        if _SUB_DISTANCE_RE.fullmatch(line):
            continue
        if _SUB_DURATION_RE.fullmatch(line):
            continue
        if line.lower().startswith(("title", "jarak", "waktu", "mode", "kecepatan")):
            continue
        wp_order += 1
        wp = _build_waypoint(sub_id, wp_order, line)
        if wp:
            sub.waypoints.append(wp)
    return sub
