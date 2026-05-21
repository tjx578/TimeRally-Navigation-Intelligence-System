"""Constraint engine - absolute binding validation.

Memeriksa:
- total distance binding,
- total time binding,
- distance binding per sub-trayek,
- time binding per sub-trayek,
- chaining finish/start,
- coordinate precision,
- route realism.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rally_core.constraints.types import ConstraintCheck, ConstraintStatus


@dataclass
class SubTrayekValidationInput:
    id: str
    label: str
    target_distance_km: float | None
    target_duration_minutes: float | None
    calculated_distance_km: float | None
    calculated_duration_minutes: float | None
    distance_counted_in_total: bool = True


@dataclass
class ChainingInput:
    sub_a_id: str
    sub_b_id: str
    finish_lat: float | None
    finish_lng: float | None
    start_lat: float | None
    start_lng: float | None


@dataclass
class ConstraintReport:
    checks: list[ConstraintCheck] = field(default_factory=list)

    @property
    def overall_status(self) -> ConstraintStatus:
        ranked = {"compliant": 0, "unchecked": 0, "warning": 1, "violation": 2, "disqualified": 3}
        worst = max((ranked.get(c.status, 0) for c in self.checks), default=0)
        for status, rank in ranked.items():
            if rank == worst:
                return status  # type: ignore[return-value]
        return "compliant"

    def to_dict(self) -> dict:
        return {
            "overall_status": self.overall_status,
            "checks": [c.__dict__ for c in self.checks],
        }


class ConstraintEngine:
    """Engine validasi rally absolute binding.

    Toleransi default:
        - jarak: 0.5 km untuk total, 0.2 km untuk sub-trayek.
        - waktu: 1 menit untuk total, 0.5 menit untuk sub-trayek.
        - chaining: 50 meter Haversine gap.
    """

    def __init__(
        self,
        total_distance_tolerance_km: float = 0.5,
        total_time_tolerance_min: float = 1.0,
        sub_distance_tolerance_km: float = 0.2,
        sub_time_tolerance_min: float = 0.5,
        chaining_tolerance_m: float = 50.0,
    ) -> None:
        self.total_distance_tolerance_km = total_distance_tolerance_km
        self.total_time_tolerance_min = total_time_tolerance_min
        self.sub_distance_tolerance_km = sub_distance_tolerance_km
        self.sub_time_tolerance_min = sub_time_tolerance_min
        self.chaining_tolerance_m = chaining_tolerance_m

    # ----- helpers -----

    def _classify_delta(self, delta_abs: float, warn_tol: float, violate_tol: float) -> ConstraintStatus:
        if delta_abs <= warn_tol:
            return "compliant"
        if delta_abs <= violate_tol:
            return "warning"
        return "violation"

    def _binding_severity(self, target: float | None, actual: float | None) -> tuple[float | None, str, int]:
        """Legacy NaviPRO championship severity: <=2% ok, 2-5% warning, >5% reject."""
        if target is None or actual is None or target == 0:
            return None, "UNCHECKED", 0
        deviation_percent = abs(actual - target) / abs(target) * 100
        if deviation_percent <= 2.0:
            return round(deviation_percent, 3), "NO_ACTION_REQUIRED", 0
        if deviation_percent <= 5.0:
            return round(deviation_percent, 3), "RECALCULATE_AND_REVIEW", 2
        return round(deviation_percent, 3), "REJECT_SOLUTION_COMPLETELY", 3

    # ----- public API -----

    def check_total_distance(
        self, target_km: float | None, calculated_km: float | None
    ) -> ConstraintCheck:
        if target_km is None or calculated_km is None:
            return ConstraintCheck(
                name="total_distance",
                status="unchecked",
                target=target_km,
                actual=calculated_km,
                unit="km",
                message="Tidak cukup data untuk validasi total jarak.",
            )
        delta = round(calculated_km - target_km, 3)
        status = self._classify_delta(
            abs(delta),
            warn_tol=self.total_distance_tolerance_km,
            violate_tol=self.total_distance_tolerance_km * 4,
        )
        message = (
            "Total jarak sesuai soal."
            if status == "compliant"
            else f"Total jarak meleset {delta:+.3f} km dari soal."
        )
        return ConstraintCheck(
            name="total_distance",
            status=status,
            target=target_km,
            actual=calculated_km,
            delta=delta,
            unit="km",
            message=message,
            severity={"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
        )

    def check_total_time(
        self, target_min: float | None, calculated_min: float | None
    ) -> ConstraintCheck:
        if target_min is None or calculated_min is None:
            return ConstraintCheck(
                name="total_time",
                status="unchecked",
                target=target_min,
                actual=calculated_min,
                unit="min",
                message="Tidak cukup data untuk validasi total waktu.",
            )
        delta = round(calculated_min - target_min, 3)
        status = self._classify_delta(
            abs(delta), self.total_time_tolerance_min, self.total_time_tolerance_min * 4
        )
        message = (
            "Total waktu sesuai soal."
            if status == "compliant"
            else f"Total waktu meleset {delta:+.2f} menit dari soal."
        )
        return ConstraintCheck(
            name="total_time",
            status=status,
            target=target_min,
            actual=calculated_min,
            delta=delta,
            unit="min",
            message=message,
            severity={"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
        )

    def check_sub_trayek(self, sub: SubTrayekValidationInput) -> list[ConstraintCheck]:
        checks: list[ConstraintCheck] = []
        if sub.target_distance_km is not None and sub.calculated_distance_km is not None:
            delta = round(sub.calculated_distance_km - sub.target_distance_km, 3)
            status = self._classify_delta(
                abs(delta), self.sub_distance_tolerance_km, self.sub_distance_tolerance_km * 4
            )
            details = self._constraint_details(
                sub.target_distance_km,
                sub.calculated_distance_km,
                "distance",
            )
            severity = max(
                {"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
                int(details["championship_severity"]),
            )
            if severity >= 3:
                status = "disqualified"
            checks.append(
                ConstraintCheck(
                    name=f"sub_distance:{sub.label}",
                    status=status,
                    target=sub.target_distance_km,
                    actual=sub.calculated_distance_km,
                    delta=delta,
                    unit="km",
                    message=(
                        f"Sub {sub.label} jarak meleset {delta:+.3f} km."
                        if status != "compliant"
                        else f"Sub {sub.label} jarak sesuai."
                    ),
                    severity=severity,
                    details=details,
                )
            )

        if sub.target_duration_minutes is not None and sub.calculated_duration_minutes is not None:
            delta = round(sub.calculated_duration_minutes - sub.target_duration_minutes, 3)
            status = self._classify_delta(
                abs(delta), self.sub_time_tolerance_min, self.sub_time_tolerance_min * 4
            )
            details = self._constraint_details(
                sub.target_duration_minutes,
                sub.calculated_duration_minutes,
                "time",
            )
            severity = max(
                {"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
                int(details["championship_severity"]),
            )
            if severity >= 3:
                status = "disqualified"
            checks.append(
                ConstraintCheck(
                    name=f"sub_time:{sub.label}",
                    status=status,
                    target=sub.target_duration_minutes,
                    actual=sub.calculated_duration_minutes,
                    delta=delta,
                    unit="min",
                    message=(
                        f"Sub {sub.label} waktu meleset {delta:+.2f} menit."
                        if status != "compliant"
                        else f"Sub {sub.label} waktu sesuai."
                    ),
                    severity=severity,
                    details=details,
                )
            )
        return checks

    def _constraint_details(
        self,
        target: float | None,
        actual: float | None,
        constraint_type: str,
    ) -> dict[str, object]:
        deviation_percent, action_required, championship_severity = self._binding_severity(target, actual)
        return {
            "constraint_type": constraint_type,
            "deviation_percent": deviation_percent,
            "championship_tolerance_percent": 2.0,
            "reject_threshold_percent": 5.0,
            "action_required": action_required,
            "championship_severity": championship_severity,
        }

    def check_chaining(self, chains: list[ChainingInput]) -> list[ConstraintCheck]:
        from rally_core.geo import haversine_meters

        checks: list[ConstraintCheck] = []
        for c in chains:
            if None in (c.finish_lat, c.finish_lng, c.start_lat, c.start_lng):
                checks.append(
                    ConstraintCheck(
                        name=f"chaining:{c.sub_a_id}->{c.sub_b_id}",
                        status="unchecked",
                        message="Koordinat finish/start belum lengkap.",
                    )
                )
                continue
            gap = haversine_meters(c.finish_lat, c.finish_lng, c.start_lat, c.start_lng)  # type: ignore[arg-type]
            status = (
                "compliant" if gap <= self.chaining_tolerance_m else
                "warning" if gap <= self.chaining_tolerance_m * 4 else
                "violation"
            )
            checks.append(
                ConstraintCheck(
                    name=f"chaining:{c.sub_a_id}->{c.sub_b_id}",
                    status=status,
                    target=0,
                    actual=gap,
                    unit="m",
                    delta=gap,
                    message=(
                        f"Gap finish->start {gap:.1f} m"
                        if status != "compliant"
                        else "Chaining presisi."
                    ),
                    severity={"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
                )
            )
        return checks

    def check_coordinate_precision(self, coordinates: list[tuple[float, float]]) -> ConstraintCheck:
        """Cek presisi koordinat - minimal 5 desimal untuk rally."""
        bad = 0
        for lat, lng in coordinates:
            lat_str = f"{lat:.6f}".rstrip("0").rstrip(".")
            lng_str = f"{lng:.6f}".rstrip("0").rstrip(".")
            lat_decimals = len(lat_str.split(".")[1]) if "." in lat_str else 0
            lng_decimals = len(lng_str.split(".")[1]) if "." in lng_str else 0
            if min(lat_decimals, lng_decimals) < 5:
                bad += 1
        status: ConstraintStatus = "compliant" if bad == 0 else "warning" if bad <= 2 else "violation"
        return ConstraintCheck(
            name="coordinate_precision",
            status=status,
            target=5,
            actual=bad,
            unit="low_precision_count",
            message=(
                f"{bad} koordinat memiliki presisi < 5 desimal."
                if bad
                else "Semua koordinat presisi minimal 5 desimal."
            ),
            severity={"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
        )

    def check_route_realism(
        self,
        straight_line_distance_km: float,
        route_distance_km: float,
    ) -> ConstraintCheck:
        """Rasio route vs straight line - rally jarang lebih dari 2.5x straight line."""
        if straight_line_distance_km <= 0:
            return ConstraintCheck(
                name="route_realism",
                status="unchecked",
                message="Straight line distance tidak tersedia.",
            )
        ratio = route_distance_km / straight_line_distance_km
        status: ConstraintStatus
        if ratio <= 1.8:
            status = "compliant"
        elif ratio <= 2.5:
            status = "warning"
        else:
            status = "violation"
        return ConstraintCheck(
            name="route_realism",
            status=status,
            target=1.8,
            actual=ratio,
            unit="ratio",
            message=f"Rasio route/straight = {ratio:.2f}",
            severity={"compliant": 0, "warning": 1, "violation": 2}.get(status, 0),
        )

    def build_report(self, checks: list[ConstraintCheck]) -> ConstraintReport:
        return ConstraintReport(checks=checks)
