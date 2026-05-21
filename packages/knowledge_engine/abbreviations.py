"""Dictionary singkatan rally - high-level wrapper.

Wrapper di atas rally_core.parser.abbreviations agar knowledge_engine bisa:
- mem-load custom dictionary dari YAML file lokal,
- mendukung override per-event,
- expose API search untuk UI editor SOP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from rally_core.parser.abbreviations import (
    CASE_SENSITIVE_TOKENS,
    LANDMARK_MODIFIERS,
    LANDMARK_TYPES,
    NAV_ACTIONS,
    SPEED_MODE_TOKENS,
)


@dataclass
class AbbreviationEntry:
    token: str
    meaning: str
    kind: str
    case_sensitive: bool = False
    examples: list[str] = field(default_factory=list)


@dataclass
class AbbreviationDictionary:
    entries: list[AbbreviationEntry] = field(default_factory=list)

    def add(self, entry: AbbreviationEntry) -> None:
        self.entries.append(entry)

    def find(self, token: str) -> list[AbbreviationEntry]:
        results: list[AbbreviationEntry] = []
        for e in self.entries:
            if e.case_sensitive and e.token == token:
                results.append(e)
            elif not e.case_sensitive and e.token.lower() == token.lower():
                results.append(e)
        return results

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [
                {
                    "token": e.token,
                    "meaning": e.meaning,
                    "kind": e.kind,
                    "case_sensitive": e.case_sensitive,
                    "examples": e.examples,
                }
                for e in self.entries
            ]
        }

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "AbbreviationDictionary":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        entries = [
            AbbreviationEntry(
                token=e["token"],
                meaning=e["meaning"],
                kind=e.get("kind", "unknown"),
                case_sensitive=bool(e.get("case_sensitive", False)),
                examples=list(e.get("examples", [])),
            )
            for e in raw.get("entries", [])
        ]
        return cls(entries=entries)


def default_abbreviation_dictionary() -> AbbreviationDictionary:
    entries: list[AbbreviationEntry] = []
    for tok, meaning in NAV_ACTIONS.items():
        entries.append(AbbreviationEntry(token=tok, meaning=meaning, kind="action"))
    for tok, meaning in LANDMARK_TYPES.items():
        entries.append(AbbreviationEntry(token=tok, meaning=meaning, kind="landmark_type"))
    for tok, info in CASE_SENSITIVE_TOKENS.items():
        entries.append(
            AbbreviationEntry(
                token=tok,
                meaning=info["value"],
                kind=info["type"],
                case_sensitive=True,
            )
        )
    for tok, meaning in LANDMARK_MODIFIERS.items():
        entries.append(AbbreviationEntry(token=tok, meaning=meaning, kind="landmark_modifier"))
    for tok, meaning in SPEED_MODE_TOKENS.items():
        entries.append(AbbreviationEntry(token=tok, meaning=meaning, kind="speed_mode"))
    return AbbreviationDictionary(entries=entries)
