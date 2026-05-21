"""Use case: parse rally text -> structured event."""

from __future__ import annotations

from rally_core import RallyParser
from rally_core.parser.models import ParseResult


_parser = RallyParser()


def parse_rally_text(raw_text: str, event_name_hint: str | None = None) -> ParseResult:
    return _parser.parse(raw_text=raw_text, event_name_hint=event_name_hint)
