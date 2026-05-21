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
_TITLE_LINE_RE = re.compile(r"(?i)^title\s*[:\-]\s*(.+)$")
_SUB_MODE_RE = re.compile(r"(?im)^(?:[*\-\s]*\*{0,2})?(?:mode|mode\s+kecepatan|kecepatan)\s*[:\-]\s*(.+)$")
_FIRST_LINE_TITLE = re.compile(r"^(.*?)(?=$|\.)")
_WAYPOINT_PREFIX_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\d+[\.)]\s*)?")
_SEGMENT_SPLIT_RE = re.compile(r"\s+[-–—]+\s+")
_TRAILING_DISTANCE_PHRASE_RE = re.compile(
    r"(?i)\b(?:dengan\s+)?jarak\s*[:,]?\s*\d+(?:[\.,]\d+)?\s*km.*$"
)
_SUB_LABEL_PREFIX_RE = re.compile(r"(?i)^\s*sub\s+([a-z]|\d+(?:\.\d+)*)\s*[:\-]?\s*")
_ROUTE_SEQUENCE_HINT_RE = re.compile(
    r"(?i)(?:\s+[-–—]+\s+|^\s*(?:start|finish|finis|akhir|bkn|bkr|jt|iju|akn|akr|ba|uj|jl\.?|jalan|br\.?)\b)"
)
_START_SEGMENT_RE = re.compile(r"(?i)^\s*(?:start|mulai)\b")
_FINISH_SEGMENT_RE = re.compile(r"(?i)^\s*(?:finish|finis|akhir|berakhir)\b")
_ENDPOINT_WORD_RE = re.compile(r"(?i)^\s*(?:start|mulai|finish|finis|akhir|berakhir)\b\s*[:\-]?")


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


def _normalize_rally_segment_text(text: str) -> str:
    text = text.replace("Â", "A").replace("Š", "S")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,.;")


def _normalize_waypoint_token_text(text: str) -> str:
    if (_is_start_segment(text) or _is_finish_segment(text)) and _has_location_payload(text):
        text = _ENDPOINT_WORD_RE.sub("", text).strip()
    text = re.sub(r"\bJ\.?\s*L\.?\s*", "Jalan ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bBR\.\s*", "br ", text)
    text = re.sub(r"^\s*BR\s+", "br ", text)
    text = re.sub(r"(?i)^\s*langsung\s+menuju\s+", "menuju ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _looks_like_route_sequence(text: str) -> bool:
    return bool(_ROUTE_SEQUENCE_HINT_RE.search(text))


def _title_payload_if_route_line(line: str) -> str | None:
    match = _TITLE_LINE_RE.match(line)
    if not match:
        return None
    payload = match.group(1).strip()
    if payload and _looks_like_route_sequence(payload):
        return payload
    return None


def _split_waypoint_segments(line: str) -> list[str]:
    """Split satu baris soal menjadi rangkaian waypoint/instruksi.

    Dalam format Time Rally lapangan, delimiter " - " memisahkan waypoint.
    Hyphen tanpa spasi tetap dibiarkan agar istilah seperti RATA-RATA tidak pecah.
    """
    line = _SUB_LABEL_PREFIX_RE.sub("", line).strip()
    line = _TRAILING_DISTANCE_PHRASE_RE.sub("", line).strip()
    if not line:
        return []

    cleaned: list[str] = []
    for part in _SEGMENT_SPLIT_RE.split(line):
        segment = _normalize_rally_segment_text(part)
        if not segment:
            continue
        if segment.lower().startswith(("dengan jarak", "jarak")):
            continue
        cleaned.append(segment)
    return cleaned


def _is_start_segment(text: str) -> bool:
    return bool(_START_SEGMENT_RE.search(text.strip()))


def _is_finish_segment(text: str) -> bool:
    return bool(_FINISH_SEGMENT_RE.search(text.strip()))


def _has_location_payload(text: str) -> bool:
    cleaned = _ENDPOINT_WORD_RE.sub("", text).strip()
    return bool(cleaned)


def _build_waypoint(
    sub_trayek_id: str,
    order: int,
    line: str,
) -> Optional[ParsedWaypoint]:
    tokens: list[WaypointToken] = tokenize_waypoint(_normalize_waypoint_token_text(line))
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


def _apply_start_finish_rules(sub: SubTrayek) -> None:
    """Isi metadata start/finish level sub berdasarkan waypoint hasil parsing.

    Chaining antar-sub dilakukan di RallyParser karena butuh akses sub sebelumnya.
    """
    if not sub.waypoints:
        sub.start_status = "missing"
        sub.finish_status = "missing"
        sub.needs_user_start = True
        sub.needs_user_finish = True
        return

    first = sub.waypoints[0]
    last = sub.waypoints[-1]

    if _is_start_segment(first.raw_text):
        sub.start_waypoint_id = first.id
        sub.start_raw_text = first.raw_text
        if _has_location_payload(first.raw_text):
            sub.start_status = "explicit"
        else:
            sub.start_status = "missing_location"
            sub.needs_user_start = True
            first.ambiguous = True
            if "start_location_required" not in first.notes:
                first.notes.append("start_location_required")
    else:
        sub.start_status = "missing"
        sub.needs_user_start = True

    explicit_finish = next((wp for wp in reversed(sub.waypoints) if _is_finish_segment(wp.raw_text)), None)
    if explicit_finish:
        sub.finish_waypoint_id = explicit_finish.id
        sub.finish_raw_text = explicit_finish.raw_text
        if _has_location_payload(explicit_finish.raw_text):
            sub.finish_status = "explicit"
        else:
            sub.finish_status = "missing"
            sub.needs_user_finish = True
            explicit_finish.ambiguous = True
            if "finish_location_required" not in explicit_finish.notes:
                explicit_finish.notes.append("finish_location_required")
        return

    if last.landmark_name or last.landmark_type or last.kmpal_marker:
        sub.finish_waypoint_id = last.id
        sub.finish_raw_text = last.raw_text
        sub.finish_status = "inferred_last_waypoint"
    else:
        sub.finish_status = "missing"
        sub.needs_user_finish = True
        last.ambiguous = True
        if "finish_location_required" not in last.notes:
            last.notes.append("finish_location_required")


def parse_sub_trayek_block(label: str, body: str, order: int) -> SubTrayek:
    sub_id = f"sub-{label.lower()}"
    sub = SubTrayek(id=sub_id, label=label, title=f"Sub {label.upper()}", raw_lines=body.splitlines())

    title_match = _SUB_TITLE_RE.search(body)
    if title_match and not _looks_like_route_sequence(title_match.group(1)):
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

    # Parse waypoint lines: skip baris metadata (dist/dur/speed mode/title).
    # Format soal asli sering memakai tanda " - " sebagai pemisah waypoint dalam satu baris.
    wp_order = 0
    for raw in body.splitlines():
        line = _clean_metadata_line(raw)
        if not line:
            continue
        if _SUB_DISTANCE_RE.fullmatch(line):
            continue
        if _SUB_DURATION_RE.fullmatch(line):
            continue
        title_route_line = _title_payload_if_route_line(line)
        if title_route_line:
            line = title_route_line
        elif line.lower().startswith(
            ("title", "jarak", "waktu", "durasi", "mode", "mode kecepatan", "kecepatan", "titik navigasi")
        ):
            continue
        line = _clean_waypoint_line(line)
        if not line:
            continue
        for segment in _split_waypoint_segments(line):
            wp_order += 1
            wp = _build_waypoint(sub_id, wp_order, segment)
            if wp:
                sub.waypoints.append(wp)
    _apply_start_finish_rules(sub)
    return sub
