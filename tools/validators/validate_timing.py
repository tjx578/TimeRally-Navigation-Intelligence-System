"""CLI validator timing table rally.

Penggunaan:

    python tools/validators/validate_timing.py data/fixtures/rally_cases/bali_trayek_1_timing_validation.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Setup PYTHONPATH agar bisa dijalankan dari root repo.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages"))

from rally_core.constraints.engine import (  # noqa: E402
    ConstraintEngine,
    SubTrayekValidationInput,
)


def validate_file(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    target_d = float(payload["declaredDistanceKm"])
    target_t = float(payload["declaredDurationMinutes"])
    rows = payload["rows"]

    counted_distance = sum(
        float(r.get("distanceKm") or 0.0)
        for r in rows
        if r.get("distanceCountedInTotal", True)
    )
    counted_duration = sum(float(r.get("durationMinutes") or 0.0) for r in rows)

    engine = ConstraintEngine()
    checks = []
    checks.append(engine.check_total_distance(target_d, counted_distance))
    checks.append(engine.check_total_time(target_t, counted_duration))
    for r in rows:
        checks.extend(
            engine.check_sub_trayek(
                SubTrayekValidationInput(
                    id=f"sub-{r['sub']}",
                    label=r["sub"],
                    target_distance_km=r.get("distanceKm"),
                    target_duration_minutes=r.get("durationMinutes"),
                    calculated_distance_km=r.get("distanceKm"),
                    calculated_duration_minutes=r.get("durationMinutes"),
                    distance_counted_in_total=bool(r.get("distanceCountedInTotal", True)),
                )
            )
        )

    failed = 0
    for c in checks:
        prefix = "OK   " if c.status == "compliant" else f"{c.status.upper():5}"
        print(f"{prefix} | {c.name:30} | {c.message}")
        if c.status in {"violation", "disqualified"}:
            failed += 1
    return 0 if failed == 0 else 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: validate_timing.py <fixture.json>")
        return 2
    target = Path(argv[1])
    if not target.is_file():
        print(f"file tidak ditemukan: {target}")
        return 2
    return validate_file(target)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
