from rally_core.constraints.engine import (
    ChainingInput,
    ConstraintEngine,
    SubTrayekValidationInput,
)


def test_total_distance_compliant_within_tolerance():
    engine = ConstraintEngine(total_distance_tolerance_km=0.5)
    check = engine.check_total_distance(target_km=93.4, calculated_km=93.6)
    assert check.status == "compliant"


def test_total_distance_warning_when_exceeding_tolerance():
    engine = ConstraintEngine(total_distance_tolerance_km=0.5)
    check = engine.check_total_distance(target_km=93.4, calculated_km=94.5)
    assert check.status == "warning"


def test_total_distance_violation_when_far():
    engine = ConstraintEngine(total_distance_tolerance_km=0.5)
    check = engine.check_total_distance(target_km=93.4, calculated_km=120.0)
    assert check.status == "violation"


def test_sub_trayek_checks_produce_both_distance_and_time():
    engine = ConstraintEngine()
    checks = engine.check_sub_trayek(
        SubTrayekValidationInput(
            id="sub-b",
            label="B",
            target_distance_km=20.1,
            target_duration_minutes=60.0,
            calculated_distance_km=20.05,
            calculated_duration_minutes=60.2,
        )
    )
    assert any(c.name == "sub_distance:B" for c in checks)
    assert any(c.name == "sub_time:B" for c in checks)


def test_chaining_close_points_compliant():
    engine = ConstraintEngine(chaining_tolerance_m=50.0)
    checks = engine.check_chaining(
        [
            ChainingInput(
                sub_a_id="sub-a",
                sub_b_id="sub-b",
                finish_lat=-8.6700,
                finish_lng=115.2210,
                start_lat=-8.6701,
                start_lng=115.2210,
            )
        ]
    )
    assert checks[0].status in {"compliant", "warning"}


def test_route_realism_flags_unrealistic_ratio():
    engine = ConstraintEngine()
    check = engine.check_route_realism(straight_line_distance_km=10.0, route_distance_km=30.0)
    assert check.status == "violation"
