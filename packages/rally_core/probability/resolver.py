"""Missing waypoint resolver.

Menyusun pipeline:
1. terima context (previous wp, missing token, next wp, target distance/time, action).
2. terima candidate pool dari place resolver / KMPAL / route graph.
3. hitung feature setiap candidate (jarak/waktu/landmark/turn/corridor/name/source).
4. skor dengan ProbabilityScorer.
5. pilih kandidat terbaik, beri decision (auto/needs_confirmation/unresolved).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from rally_core.geo import haversine_km
from rally_core.probability.decision import Decision, classify_confidence
from rally_core.probability.scorer import CandidateFeatures, ProbabilityScorer


@dataclass
class WaypointAnchor:
    id: str
    lat: float
    lng: float
    name: str | None = None


@dataclass
class MissingWaypointContext:
    missing_text: str
    previous: WaypointAnchor
    next: WaypointAnchor
    target_distance_km: float | None = None
    target_time_seconds: float | None = None
    navigation_action: str | None = None
    landmark_type_hint: str | None = None
    text_context: str = ""


@dataclass
class CandidatePlace:
    id: str
    name: str
    lat: float
    lng: float
    landmark_type: str | None = None
    source: str = "unknown"  # local, kmpal, osm, google, inferred, marshal
    route_corridor_fit: float = 0.5
    turn_geometry_fit: float = 0.5
    name_context_match: float = 0.5
    metadata: dict = field(default_factory=dict)


SOURCE_QUALITY = {
    "local": 1.0,
    "kmpal": 0.95,
    "curated": 0.9,
    "osm": 0.8,
    "nominatim": 0.75,
    "google": 0.7,
    "inferred": 0.55,
    "marshal": 0.85,
    "unknown": 0.4,
}

LANDMARK_TYPE_MATCH = {
    "O": "bundaran",
    "X": "simpang_empat",
    "T": "simpang_tiga",
    "br": "banjar",
    "POM": "spbu",
    "SDN": "sekolah_dasar",
    "SMP": "sekolah_menengah_pertama",
    "SMA": "sekolah_menengah_atas",
    "SMK": "sekolah_menengah_kejuruan",
}


@dataclass
class CandidateEvaluation:
    candidate: CandidatePlace
    score: float
    decision: Decision
    confidence: float
    distance_deviation_percent: float
    time_deviation_seconds: float
    reasons: list[str]


@dataclass
class ResolveResult:
    selected: CandidateEvaluation | None
    alternatives: list[CandidateEvaluation]
    decision: Decision
    note: str

    def to_dict(self) -> dict:
        return {
            "selected": _eval_to_dict(self.selected) if self.selected else None,
            "alternatives": [_eval_to_dict(e) for e in self.alternatives],
            "decision": self.decision,
            "note": self.note,
        }


def _eval_to_dict(e: CandidateEvaluation) -> dict:
    return {
        "candidate": {
            "id": e.candidate.id,
            "name": e.candidate.name,
            "lat": e.candidate.lat,
            "lng": e.candidate.lng,
            "landmark_type": e.candidate.landmark_type,
            "source": e.candidate.source,
        },
        "score": e.score,
        "confidence": e.confidence,
        "decision": e.decision,
        "distance_deviation_percent": e.distance_deviation_percent,
        "time_deviation_seconds": e.time_deviation_seconds,
        "reasons": e.reasons,
    }


class MissingWaypointResolver:
    """Resolver waypoint hilang sesuai docs/MISSING_WAYPOINT_PROBABILITY.md."""

    def __init__(self, scorer: ProbabilityScorer | None = None) -> None:
        self.scorer = scorer or ProbabilityScorer()

    # ----- feature builders -----

    def _landmark_type_match(self, hint: str | None, candidate_type: str | None) -> float:
        if not hint:
            return 0.5
        canonical = LANDMARK_TYPE_MATCH.get(hint, hint).lower()
        if candidate_type is None:
            return 0.3
        cand = candidate_type.lower()
        if canonical == cand:
            return 1.0
        if canonical in cand or cand in canonical:
            return 0.75
        return 0.2

    def _name_context_fit(self, candidate: CandidatePlace, context: MissingWaypointContext) -> float:
        ctx = context.text_context.lower()
        if not ctx:
            return candidate.name_context_match
        name = candidate.name.lower()
        if not name:
            return candidate.name_context_match
        tokens = [t for t in name.replace(",", " ").split() if len(t) >= 3]
        if not tokens:
            return candidate.name_context_match
        hits = sum(1 for t in tokens if t in ctx)
        return min(1.0, hits / max(1, len(tokens)))

    def _distance_deviation_percent(
        self, context: MissingWaypointContext, candidate: CandidatePlace
    ) -> float:
        if context.target_distance_km is None or context.target_distance_km <= 0:
            return 0.0
        d_prev = haversine_km(
            context.previous.lat, context.previous.lng, candidate.lat, candidate.lng
        )
        d_next = haversine_km(
            candidate.lat, candidate.lng, context.next.lat, context.next.lng
        )
        actual = d_prev + d_next
        return abs(actual - context.target_distance_km) / context.target_distance_km * 100.0

    def _time_deviation_seconds(
        self, context: MissingWaypointContext, candidate: CandidatePlace
    ) -> float:
        if context.target_time_seconds is None:
            return 0.0
        # Asumsi 40 km/jam rata-rata jika tidak ada data lain.
        avg_kmh = 40.0
        d_prev = haversine_km(
            context.previous.lat, context.previous.lng, candidate.lat, candidate.lng
        )
        d_next = haversine_km(
            candidate.lat, candidate.lng, context.next.lat, context.next.lng
        )
        actual_time_s = (d_prev + d_next) / avg_kmh * 3600.0
        return abs(actual_time_s - context.target_time_seconds)

    def _build_features(
        self, context: MissingWaypointContext, candidate: CandidatePlace
    ) -> tuple[CandidateFeatures, float, float]:
        dist_dev = self._distance_deviation_percent(context, candidate)
        time_dev = self._time_deviation_seconds(context, candidate)
        features = CandidateFeatures(
            distance_deviation_percent=dist_dev,
            time_deviation_seconds=time_dev,
            landmark_type_match=self._landmark_type_match(
                context.landmark_type_hint, candidate.landmark_type
            ),
            turn_geometry_match=candidate.turn_geometry_fit,
            route_corridor_fit=candidate.route_corridor_fit,
            name_context_fit=self._name_context_fit(candidate, context),
            source_quality=SOURCE_QUALITY.get(candidate.source, 0.5),
        )
        return features, dist_dev, time_dev

    # ----- public API -----

    def evaluate(
        self,
        context: MissingWaypointContext,
        candidates: Iterable[CandidatePlace],
        max_alternatives: int = 5,
    ) -> ResolveResult:
        evaluations: list[CandidateEvaluation] = []
        for cand in candidates:
            features, dist_dev, time_dev = self._build_features(context, cand)
            confidence = self.scorer.score(features)
            decision = classify_confidence(confidence)
            evaluations.append(
                CandidateEvaluation(
                    candidate=cand,
                    score=confidence,
                    confidence=confidence,
                    decision=decision,
                    distance_deviation_percent=dist_dev,
                    time_deviation_seconds=time_dev,
                    reasons=self.scorer.explain(features),
                )
            )
        evaluations.sort(key=lambda e: e.confidence, reverse=True)
        selected = evaluations[0] if evaluations else None
        alternatives = evaluations[1 : 1 + max_alternatives]
        decision: Decision = selected.decision if selected else "unresolved"
        note = (
            "Auto select inferred (confidence >= 0.85)"
            if decision == "auto_select_inferred"
            else "Butuh konfirmasi navigator/analyst"
            if decision == "needs_confirmation"
            else "Tidak ada kandidat yang cukup yakin"
        )
        return ResolveResult(
            selected=selected,
            alternatives=alternatives,
            decision=decision,
            note=note,
        )
