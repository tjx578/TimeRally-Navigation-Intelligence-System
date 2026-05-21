from knowledge_engine import KMPALDatabase
from rally_core.constraints.engine import ConstraintEngine, SubTrayekValidationInput
from rally_core.parser.tokenizer import tokenize_waypoint
from rally_core.scoring.engine import ChampionshipPointsInput, ChampionshipScorer


def test_tokenizer_detects_standalone_kmpal_pairs():
    tokens = tokenize_waypoint("BKR di KSM 2 lalu JT di DPS 11")
    markers = [token.value for token in tokens if token.kind == "kmpal"]
    assert markers == ["KSM 2", "DPS 11"]


def test_kmpal_extract_markers_from_compound_text():
    db = KMPALDatabase.from_yaml_file("data/curated/kmpal/bali_sample.yaml")
    points = db.extract_markers("KSM 2/DPS 11/PNT 0 finish")
    assert [point.code for point in points] == ["KSM", "DPS", "PNT"]


def test_binding_enforcer_adds_championship_action_details():
    engine = ConstraintEngine()
    checks = engine.check_sub_trayek(
        SubTrayekValidationInput(
            id="sub-b",
            label="B",
            target_distance_km=20.0,
            target_duration_minutes=60.0,
            calculated_distance_km=22.0,
            calculated_duration_minutes=60.0,
        )
    )
    distance = next(check for check in checks if check.name == "sub_distance:B")
    assert distance.status == "disqualified"
    assert distance.details["action_required"] == "REJECT_SOLUTION_COMPLETELY"


def test_championship_points_can_reach_ready_classification():
    score = ChampionshipScorer().score_points(
        ChampionshipPointsInput(
            target_distance_km=20.0,
            calculated_distance_km=20.1,
            time_distance_km=20.1,
            actual_minutes=60.0,
            speed_kmh=20.1,
            chaining_gaps_m=[2.0, 4.5, 6.0],
            coordinates=[(-8.650123, 115.216789), (-8.651234, 115.217891)],
            knowledge_hits=9,
            knowledge_total=10,
            map_validation_ready=True,
            output_formats=["yaml", "gpx", "kml", "geojson", "roadbook.md"],
            google_maps_links_tested=True,
        )
    )
    assert score.total_score >= 500
    assert score.verdict == "ready"
