"""Decision rule untuk hasil probability resolver.

confidence >= 0.85 -> auto_select_inferred
0.70 <= confidence < 0.85 -> needs_confirmation
confidence < 0.70 -> unresolved
"""

from __future__ import annotations

from typing import Literal


Decision = Literal["auto_select_inferred", "needs_confirmation", "unresolved"]


def classify_confidence(confidence: float) -> Decision:
    if confidence >= 0.85:
        return "auto_select_inferred"
    if confidence >= 0.70:
        return "needs_confirmation"
    return "unresolved"
