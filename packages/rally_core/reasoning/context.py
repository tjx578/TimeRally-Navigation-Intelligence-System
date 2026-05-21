"""Context resolver untuk parsing rally.

Bertanggung jawab menghasilkan interpretasi token dalam konteks kalimat.
Contoh konteks:
    - "BR" di awal kalimat dengan "menuju" berarti arah Barat.
    - "br" sebelum nama desa berarti landmark Banjar.
    - "X LR" berarti simpang empat berlampu.
    - "BKN di O" berarti belok kanan di bundaran.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rally_core.parser.models import ParsedWaypoint
from rally_core.parser.abbreviations import (
    CASE_SENSITIVE_TOKENS,
    LANDMARK_MODIFIERS,
    LANDMARK_TYPES,
    NAV_ACTIONS,
    get_direction,
)
from rally_core.reasoning.ambiguity import AmbiguityLedger, AmbiguityNote


@dataclass
class ResolvedToken:
    raw: str
    canonical: str
    kind: str
    confidence: float
    rationale: str
    alternatives: list[str] = field(default_factory=list)


class ContextResolver:
    """Resolver yang menerjemahkan token rally menjadi makna canonical.

    ContextResolver berhubungan erat dengan parser tetapi dipisah agar
    bisa dipakai independen oleh probability resolver, route editor, dan UI.
    """

    def __init__(self, ledger: AmbiguityLedger | None = None) -> None:
        self.ledger = ledger or AmbiguityLedger()

    def resolve(self, token: str, *, waypoint_id: str | None = None) -> ResolvedToken:
        if token in CASE_SENSITIVE_TOKENS:
            info = CASE_SENSITIVE_TOKENS[token]
            kind = "landmark_type" if info["type"] == "landmark" else "direction"
            return ResolvedToken(
                raw=token,
                canonical=info["value"],
                kind=kind,
                confidence=0.99,
                rationale=f"Token case-sensitive '{token}' map ke {kind}.",
            )

        upper = token.upper()
        if upper in NAV_ACTIONS:
            return ResolvedToken(
                raw=token,
                canonical=NAV_ACTIONS[upper],
                kind="action",
                confidence=0.97,
                rationale="Nav action canonical.",
            )
        if upper in LANDMARK_TYPES:
            return ResolvedToken(
                raw=token,
                canonical=LANDMARK_TYPES[upper],
                kind="landmark_type",
                confidence=0.95,
                rationale="Tipe landmark canonical.",
            )
        if upper in LANDMARK_MODIFIERS:
            return ResolvedToken(
                raw=token,
                canonical=LANDMARK_MODIFIERS[upper],
                kind="landmark_modifier",
                confidence=0.9,
                rationale="Modifier landmark canonical.",
            )

        direction = get_direction(token)
        if direction:
            return ResolvedToken(
                raw=token,
                canonical=direction,
                kind="direction",
                confidence=0.9,
                rationale="Arah mata angin (case sensitive).",
            )

        # Fallback ambigu
        note = AmbiguityNote(
            waypoint_id=waypoint_id,
            token=token,
            interpretations=["unknown_token"],
            severity="warning",
            suggestion="Tambahkan ke knowledge_engine.abbreviations jika ini singkatan baru.",
        )
        self.ledger.add(note)
        return ResolvedToken(
            raw=token,
            canonical=token,
            kind="unknown",
            confidence=0.0,
            rationale="Token tidak dikenal di kamus singkatan rally.",
            alternatives=[],
        )

    def annotate_waypoint(self, wp: ParsedWaypoint) -> ParsedWaypoint:
        """Tambahkan note konteks ke waypoint hasil parser."""
        if wp.landmark_type == "bundaran" and wp.action is None:
            self.ledger.add(
                AmbiguityNote(
                    waypoint_id=wp.id,
                    token=wp.raw_text,
                    interpretations=["bundaran tanpa instruksi belok"],
                    severity="info",
                    suggestion="Confirm aksi (BKN/BKR/JT) jika perlu.",
                )
            )
        if wp.landmark_name and wp.landmark_name.lower().startswith("br "):
            self.ledger.add(
                AmbiguityNote(
                    waypoint_id=wp.id,
                    token=wp.landmark_name,
                    interpretations=["banjar (br) vs arah barat (BR)"],
                    severity="warning",
                    suggestion="Cek case-sensitivity teks asli.",
                )
            )
        return wp
