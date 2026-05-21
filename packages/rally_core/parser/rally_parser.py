"""Main entrypoint parser rally.

RallyParser memadukan normalizer, structure detector, dan sub-trayek parser
untuk menghasilkan ParseResult yang utuh.
"""

from __future__ import annotations

from rally_core.parser.models import (
    ParseResult,
    RallyEvent,
    UnresolvedToken,
)
from rally_core.parser.normalizer import (
    normalize_rally_text,
    split_sub_trayek_blocks,
)
from rally_core.parser.structure import detect_header
from rally_core.parser.sub_trayek import parse_sub_trayek_block


class RallyParser:
    """Parser soal rally - tidak melakukan resolusi koordinat / routing."""

    def __init__(self, default_event_name: str = "Untitled Rally Event") -> None:
        self.default_event_name = default_event_name

    def parse(self, raw_text: str, event_name_hint: str | None = None) -> ParseResult:
        normalized = normalize_rally_text(raw_text)
        header = detect_header(normalized)
        event = RallyEvent(
            event_name=event_name_hint or header.event_name or self.default_event_name,
            trayek_name=header.trayek_name,
            location=header.location,
            total_distance_km=header.total_distance_km,
            total_time_minutes=header.total_time_minutes,
            rally_start_time=header.rally_start_time,
            normalized_text=normalized,
        )

        blocks = split_sub_trayek_blocks(normalized)
        warnings: list[str] = []
        unresolved: list[UnresolvedToken] = []

        for idx, (label, body) in enumerate(blocks):
            sub = parse_sub_trayek_block(label=label, body=body, order=idx)
            event.sub_trayeks.append(sub)
            for wp in sub.waypoints:
                if wp.ambiguous:
                    unresolved.append(
                        UnresolvedToken(
                            token=wp.raw_text,
                            sub_trayek_id=sub.id,
                            line_index=wp.order,
                            reason="no_recognizable_token",
                        )
                    )

        if not blocks:
            warnings.append(
                "Tidak ada blok Sub yang terdeteksi. Pastikan soal memuat baris 'Sub A', 'Sub B', dst."
            )

        # Cross-check total
        if event.total_distance_km is not None:
            computed = sum(
                s.distance_km
                for s in event.sub_trayeks
                if s.distance_km is not None and s.distance_counted_in_total
            )
            if computed and abs(computed - event.total_distance_km) > 0.5:
                warnings.append(
                    f"Total jarak dari sub-trayek ({computed:.2f} km) tidak cocok dengan total soal ({event.total_distance_km:.2f} km)."
                )

        if event.total_time_minutes is not None:
            computed_t = sum(s.duration_minutes for s in event.sub_trayeks if s.duration_minutes is not None)
            if computed_t and abs(computed_t - event.total_time_minutes) > 1.0:
                warnings.append(
                    f"Total waktu dari sub-trayek ({computed_t:.1f} menit) tidak cocok dengan total soal ({event.total_time_minutes:.1f} menit)."
                )

        return ParseResult(event=event, unresolved_tokens=unresolved, warnings=warnings)
