"""Pencatat ambiguity rally.

Setiap kali parser/reasoner menemukan situasi yang membutuhkan konfirmasi
manusia, catat AmbiguityNote ke ledger. Ledger akan muncul di output final
sebagai bagian dari candidate-review report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Severity = Literal["info", "warning", "blocker"]


@dataclass
class AmbiguityNote:
    waypoint_id: str | None
    token: str
    interpretations: list[str]
    severity: Severity = "warning"
    suggestion: str | None = None
    source: str = "reasoning"


@dataclass
class AmbiguityLedger:
    notes: list[AmbiguityNote] = field(default_factory=list)

    def add(self, note: AmbiguityNote) -> None:
        self.notes.append(note)

    def blockers(self) -> list[AmbiguityNote]:
        return [n for n in self.notes if n.severity == "blocker"]

    def warnings(self) -> list[AmbiguityNote]:
        return [n for n in self.notes if n.severity == "warning"]

    def to_list(self) -> list[dict]:
        return [
            {
                "waypoint_id": n.waypoint_id,
                "token": n.token,
                "interpretations": n.interpretations,
                "severity": n.severity,
                "suggestion": n.suggestion,
                "source": n.source,
            }
            for n in self.notes
        ]
