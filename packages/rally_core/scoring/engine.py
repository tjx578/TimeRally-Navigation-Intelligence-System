"""Championship scoring engine.

Komponen score sesuai docs/WINNING_SYSTEM_BLUEPRINT.md:
- distance compliance
- time formula accuracy
- waypoint chaining
- coordinate precision
- knowledge hit rate
- map validation (Google/OSM agreement)
- output completeness
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from rally_core.constraints.engine import ConstraintReport


ReadinessVerdict = Literal["ready", "marginal", "not_ready"]


@dataclass
class ChampionshipScoreInput:
    distance_compliance: float  # 0..1
    time_formula_accuracy: float  # 0..1
    waypoint_chaining: float  # 0..1
    coordinate_precision: float  # 0..1
    knowledge_hit_rate: float  # 0..1
    map_validation: float  # 0..1
    output_completeness: float  # 0..1


WEIGHTS = {
    "distance_compliance": 0.20,
    "time_formula_accuracy": 0.20,
    "waypoint_chaining": 0.15,
    "coordinate_precision": 0.10,
    "knowledge_hit_rate": 0.10,
    "map_validation": 0.15,
    "output_completeness": 0.10,
}


@dataclass
class ChampionshipScore:
    total: float
    components: dict[str, float]
    penalties: list[str] = field(default_factory=list)
    verdict: ReadinessVerdict = "marginal"

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "components": self.components,
            "penalties": self.penalties,
            "verdict": self.verdict,
        }


class ChampionshipScorer:
    """Scorer championship readiness."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or dict(WEIGHTS)
        total_weight = sum(self.weights.values())
        if not 0.99 <= total_weight <= 1.01:
            raise ValueError(f"Total weight harus = 1.0, dapat {total_weight}")

    def score(self, components: ChampionshipScoreInput) -> ChampionshipScore:
        comp_dict = {
            "distance_compliance": components.distance_compliance,
            "time_formula_accuracy": components.time_formula_accuracy,
            "waypoint_chaining": components.waypoint_chaining,
            "coordinate_precision": components.coordinate_precision,
            "knowledge_hit_rate": components.knowledge_hit_rate,
            "map_validation": components.map_validation,
            "output_completeness": components.output_completeness,
        }
        total = sum(self.weights[k] * v for k, v in comp_dict.items())
        penalties: list[str] = []
        for name, value in comp_dict.items():
            if value < 0.5:
                penalties.append(f"komponen {name} di bawah ambang minimum (<0.5)")

        if total >= 0.9 and not penalties:
            verdict: ReadinessVerdict = "ready"
        elif total >= 0.7:
            verdict = "marginal"
        else:
            verdict = "not_ready"

        return ChampionshipScore(
            total=round(total, 4),
            components={k: round(v, 4) for k, v in comp_dict.items()},
            penalties=penalties,
            verdict=verdict,
        )

    @staticmethod
    def derive_from_constraints(report: ConstraintReport) -> ChampionshipScoreInput:
        """Helper: turunkan rough score dari ConstraintReport.

        Berguna ketika sistem sudah punya hasil validasi tetapi belum semua
        komponen lain terhitung.
        """
        def _ratio(name_prefix: str) -> float:
            relevant = [c for c in report.checks if c.name.startswith(name_prefix)]
            if not relevant:
                return 0.5
            ok = sum(1 for c in relevant if c.status == "compliant")
            return ok / len(relevant)

        return ChampionshipScoreInput(
            distance_compliance=_ratio("total_distance") * 0.6 + _ratio("sub_distance") * 0.4,
            time_formula_accuracy=_ratio("total_time") * 0.6 + _ratio("sub_time") * 0.4,
            waypoint_chaining=_ratio("chaining"),
            coordinate_precision=_ratio("coordinate_precision"),
            knowledge_hit_rate=0.7,
            map_validation=_ratio("route_realism"),
            output_completeness=0.7,
        )
