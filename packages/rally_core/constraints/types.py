"""Type alias dan dataclass untuk constraint engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


ConstraintStatus = Literal["compliant", "warning", "violation", "disqualified", "unchecked"]


@dataclass
class ConstraintCheck:
    name: str
    status: ConstraintStatus
    target: float | None = None
    actual: float | None = None
    delta: float | None = None
    unit: str | None = None
    message: str = ""
    severity: int = 0  # 0 ok, 1 warning, 2 violation, 3 disqualified
    details: dict[str, object] = field(default_factory=dict)
