"""Probability scorer untuk missing waypoint.

Formula default mengikuti docs/MISSING_WAYPOINT_PROBABILITY.md:

    score =
      0.35 * time_distance_fit
    + 0.20 * landmark_type_fit
    + 0.15 * turn_geometry_fit
    + 0.15 * route_corridor_fit
    + 0.10 * name_context_fit
    + 0.05 * source_quality
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp


@dataclass
class CandidateFeatures:
    distance_deviation_percent: float = 0.0  # 0 = pas
    time_deviation_seconds: float = 0.0
    landmark_type_match: float = 0.0  # 0..1
    turn_geometry_match: float = 0.0  # 0..1
    route_corridor_fit: float = 0.0  # 0..1
    name_context_fit: float = 0.0  # 0..1
    source_quality: float = 0.5  # 0..1


@dataclass
class ScoringWeights:
    time_distance: float = 0.35
    landmark_type: float = 0.20
    turn_geometry: float = 0.15
    route_corridor: float = 0.15
    name_context: float = 0.10
    source_quality: float = 0.05


class ProbabilityScorer:
    def __init__(self, weights: ScoringWeights | None = None) -> None:
        self.weights = weights or ScoringWeights()

    @staticmethod
    def time_distance_fit(features: CandidateFeatures) -> float:
        """Konversi deviasi (%) jarak dan deviasi (detik) waktu menjadi fit 0..1.

        Pakai gaussian-like: exp(-deviation^2 / scale^2).
        """
        dist_term = exp(-(features.distance_deviation_percent ** 2) / (6.0 ** 2))
        time_term = exp(-(features.time_deviation_seconds ** 2) / (120.0 ** 2))
        return 0.5 * dist_term + 0.5 * time_term

    def score(self, features: CandidateFeatures) -> float:
        td = self.time_distance_fit(features)
        w = self.weights
        s = (
            w.time_distance * td
            + w.landmark_type * features.landmark_type_match
            + w.turn_geometry * features.turn_geometry_match
            + w.route_corridor * features.route_corridor_fit
            + w.name_context * features.name_context_fit
            + w.source_quality * features.source_quality
        )
        return max(0.0, min(1.0, round(s, 4)))

    def explain(self, features: CandidateFeatures) -> list[str]:
        reasons: list[str] = []
        td = self.time_distance_fit(features)
        if td >= 0.85:
            reasons.append(f"distance deviation {features.distance_deviation_percent:.1f}% dan waktu {features.time_deviation_seconds:.0f}s pas")
        else:
            reasons.append(f"distance deviation {features.distance_deviation_percent:.1f}%, time deviation {features.time_deviation_seconds:.0f}s")
        if features.landmark_type_match >= 0.8:
            reasons.append("landmark type cocok dengan token soal")
        elif features.landmark_type_match >= 0.5:
            reasons.append("landmark type cukup cocok dengan token soal")
        if features.turn_geometry_match >= 0.8:
            reasons.append("bentuk jalan mendukung instruksi belok soal")
        if features.route_corridor_fit >= 0.8:
            reasons.append("kandidat berada di koridor route A->C")
        if features.name_context_fit >= 0.7:
            reasons.append("nama area cocok dengan teks sekitar")
        if features.source_quality >= 0.9:
            reasons.append("sumber tergolong verified")
        return reasons
