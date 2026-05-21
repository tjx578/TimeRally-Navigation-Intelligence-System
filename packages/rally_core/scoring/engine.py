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


@dataclass
class ChampionshipPointsInput:
    """Input scoring legacy NaviPRO 600 poin.

    Skor ini dipakai sebagai indikator race-day: makin tinggi makin dekat ke
    solusi yang layak dipakai untuk lomba, bukan sekadar "parse berhasil".
    """

    target_distance_km: float
    calculated_distance_km: float
    time_distance_km: float
    actual_minutes: float
    speed_kmh: float
    chaining_gaps_m: list[float] = field(default_factory=list)
    coordinates: list[tuple[float, float]] = field(default_factory=list)
    knowledge_hits: int = 0
    knowledge_total: int = 0
    map_validation_ready: bool = False
    output_formats: list[str] = field(default_factory=list)
    google_maps_links_tested: bool = False


@dataclass
class ChampionshipPointsScore:
    total_score: int
    max_possible_score: int
    classification: str
    components: dict[str, int]
    diagnostics: dict[str, object] = field(default_factory=dict)
    verdict: ReadinessVerdict = "marginal"

    def to_dict(self) -> dict:
        return {
            "total_score": self.total_score,
            "max_possible_score": self.max_possible_score,
            "classification": self.classification,
            "components": self.components,
            "diagnostics": self.diagnostics,
            "verdict": self.verdict,
        }


class ChampionshipScorer:
    """Scorer championship readiness."""

    POINT_CLASSIFICATION_THRESHOLDS = {
        550: "JUARA NASIONAL",
        500: "TINGKAT PROVINSI",
        450: "TINGKAT KOTA",
        400: "PESERTA AKTIF",
        350: "PERLU LATIHAN",
        0: "TIDAK MEMENUHI SYARAT",
    }

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
    def _threshold_score(value: float, thresholds: list[tuple[float, int]]) -> int:
        for threshold, score in thresholds:
            if value <= threshold:
                return score
        return 0

    @staticmethod
    def _coordinate_precision_score(coordinates: list[tuple[float, float]]) -> tuple[int, dict[str, object]]:
        if not coordinates:
            return 0, {"precision_level": "NO_COORDINATES"}
        placeholder_count = sum(1 for lat, lng in coordinates if lat == 0.0 and lng == 0.0)
        if placeholder_count:
            return 0, {"precision_level": "PLACEHOLDER_DETECTED", "placeholder_count": placeholder_count}

        decimal_places: list[int] = []
        for lat, lng in coordinates:
            lat_decimals = len(f"{lat:.8f}".rstrip("0").split(".")[-1])
            lng_decimals = len(f"{lng:.8f}".rstrip("0").split(".")[-1])
            decimal_places.append(min(lat_decimals, lng_decimals))
        avg_decimals = sum(decimal_places) / len(decimal_places)
        if avg_decimals >= 6:
            return 100, {"precision_level": "ULTRA_PRECISION", "average_decimal_places": avg_decimals}
        if avg_decimals >= 4:
            return 90, {"precision_level": "HIGH_PRECISION", "average_decimal_places": avg_decimals}
        if avg_decimals >= 2:
            return 80, {"precision_level": "STANDARD_PRECISION", "average_decimal_places": avg_decimals}
        return 0, {"precision_level": "LOW_PRECISION", "average_decimal_places": avg_decimals}

    @staticmethod
    def _knowledge_bonus(hits: int, total: int) -> tuple[int, dict[str, object]]:
        if total <= 0:
            return 0, {"hit_rate": 0.0, "status": "NO_LOOKUPS"}
        hit_rate = hits / total * 100
        if hit_rate >= 90:
            bonus = 20
        elif hit_rate >= 80:
            bonus = 15
        elif hit_rate >= 70:
            bonus = 10
        elif hit_rate >= 60:
            bonus = 5
        else:
            bonus = 0
        return bonus, {"hit_rate": round(hit_rate, 1), "hits": hits, "total": total}

    def score_points(self, payload: ChampionshipPointsInput) -> ChampionshipPointsScore:
        """Hitung score championship 600 poin dari logic legacy NaviPRO."""
        if payload.target_distance_km <= 0:
            distance_score = 0
            distance_diag: dict[str, object] = {"status": "ERROR_ZERO_TARGET"}
        else:
            distance_dev = abs(payload.calculated_distance_km - payload.target_distance_km) / payload.target_distance_km * 100
            distance_raw = self._threshold_score(
                distance_dev,
                [(0.0, 100), (1.0, 95), (2.0, 85), (3.0, 70), (5.0, 50), (float("inf"), 0)],
            )
            distance_score = int(distance_raw * 1.5)
            distance_diag = {"deviation_percent": round(distance_dev, 3)}

        if payload.speed_kmh <= 0:
            time_score = 0
            time_diag: dict[str, object] = {"status": "ERROR_ZERO_SPEED"}
        else:
            expected_minutes = payload.time_distance_km * 60 / payload.speed_kmh
            time_dev = abs(payload.actual_minutes - expected_minutes)
            time_score = self._threshold_score(
                time_dev,
                [(0.5, 100), (1.0, 90), (2.0, 80), (3.0, 70), (5.0, 50), (float("inf"), 0)],
            )
            time_diag = {"expected_minutes": round(expected_minutes, 2), "deviation_minutes": round(time_dev, 3)}

        if payload.chaining_gaps_m:
            avg_gap = sum(payload.chaining_gaps_m) / len(payload.chaining_gaps_m)
            max_gap = max(payload.chaining_gaps_m)
            chaining_score = self._threshold_score(
                avg_gap,
                [(5.0, 100), (10.0, 95), (20.0, 85), (50.0, 70), (100.0, 50), (float("inf"), 0)],
            )
            continuity_score = 50 if max_gap <= 20 else 35 if max_gap <= 50 else 0
            chaining_diag: dict[str, object] = {"average_gap_m": round(avg_gap, 2), "max_gap_m": round(max_gap, 2)}
        else:
            chaining_score = 0
            continuity_score = 0
            chaining_diag = {"status": "NO_CHAINING_DATA"}

        precision_score, precision_diag = self._coordinate_precision_score(payload.coordinates)
        knowledge_bonus, knowledge_diag = self._knowledge_bonus(payload.knowledge_hits, payload.knowledge_total)
        map_bonus = 30 if payload.map_validation_ready else 0
        output_bonus = min(30, len(set(payload.output_formats)) * 6)
        google_bonus = 20 if payload.google_maps_links_tested else 0

        components = {
            "distance_compliance": distance_score,
            "time_formula_accuracy": time_score,
            "waypoint_chaining": chaining_score,
            "coordinate_precision": precision_score,
            "sequential_continuity": continuity_score,
            "knowledge_efficiency_bonus": knowledge_bonus,
            "real_route_validation_bonus": map_bonus,
            "output_completeness_bonus": output_bonus,
            "google_maps_integration_bonus": google_bonus,
        }
        total_score = min(600, sum(components.values()))
        classification = next(
            label
            for threshold, label in self.POINT_CLASSIFICATION_THRESHOLDS.items()
            if total_score >= threshold
        )
        verdict: ReadinessVerdict = (
            "ready" if total_score >= 500 else "marginal" if total_score >= 400 else "not_ready"
        )
        return ChampionshipPointsScore(
            total_score=total_score,
            max_possible_score=600,
            classification=classification,
            components=components,
            diagnostics={
                "distance": distance_diag,
                "time": time_diag,
                "chaining": chaining_diag,
                "coordinate_precision": precision_diag,
                "knowledge": knowledge_diag,
            },
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
