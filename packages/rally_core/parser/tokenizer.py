"""Tokenizer waypoint rally.

Tugas tokenizer:
- memecah satu baris waypoint menjadi sequence token,
- mempertahankan case-sensitive distinction (BR vs br),
- mengenali KMPAL pattern (CT 7/PNT 0/KSM 2),
- mengenali nav action, landmark, modifier, dan landmark name lepas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rally_core.parser import abbreviations as ab


_TOKEN_RE = re.compile(r"[A-Za-z]+(?:\.[A-Za-z]+)*|\d+(?:[\.,]\d+)?|[A-Za-z]+\d+|[^\s]")
_KMPAL_PART = re.compile(r"^[A-Z]{2,4}\s*\d+(?:[\.,]\d+)?$")


@dataclass
class WaypointToken:
    text: str
    kind: str  # action, landmark_type, landmark_modifier, direction, relation, kmpal, name, number, separator
    value: str | None = None


def _classify(token: str) -> tuple[str, str | None]:
    raw = token
    if ab.is_nav_action(raw):
        return "action", ab.normalize_action(raw)
    if raw in ab.CASE_SENSITIVE_TOKENS:
        info = ab.CASE_SENSITIVE_TOKENS[raw]
        if info["type"] == "landmark":
            return "landmark_type", info["value"]
        return "direction", info["value"]
    lm = ab.normalize_landmark_type(raw)
    if lm is not None:
        return "landmark_type", lm
    if ab.is_landmark_modifier(raw):
        return "landmark_modifier", ab.LANDMARK_MODIFIERS[raw.upper()]
    if raw.lower() in ab.RELATION_PREPS:
        return "relation", ab.RELATION_PREPS[raw.lower()]
    if raw.replace(",", ".").replace(".", "").isdigit():
        return "number", raw.replace(",", ".")
    return "name", None


def tokenize_waypoint(line: str) -> list[WaypointToken]:
    """Memecah satu baris waypoint menjadi token rally.

    Token KMPAL ditangani khusus karena bisa multi-fragment (KSM 2/DPS 11/PNT 0).
    """
    tokens: list[WaypointToken] = []
    line = line.strip()
    if not line:
        return tokens

    # Pisahkan KMPAL pattern (X 2/Y 11/Z 0)
    kmpal_match = re.search(r"\b([A-Z]{2,4}\s*\d+(?:[\.,]\d+)?(?:\s*/\s*[A-Z]{2,4}\s*\d+(?:[\.,]\d+)?)+)\b", line)
    if kmpal_match:
        before = line[: kmpal_match.start()].strip()
        kmpal_text = kmpal_match.group(1).strip()
        after = line[kmpal_match.end() :].strip()
        tokens.extend(tokenize_waypoint(before))
        tokens.append(WaypointToken(text=kmpal_text, kind="kmpal", value=kmpal_text))
        tokens.extend(tokenize_waypoint(after))
        return tokens

    for raw in _TOKEN_RE.findall(line):
        if raw in {",", ";", ":"}:
            tokens.append(WaypointToken(text=raw, kind="separator"))
            continue
        kind, value = _classify(raw)
        tokens.append(WaypointToken(text=raw, kind=kind, value=value))
    return tokens
