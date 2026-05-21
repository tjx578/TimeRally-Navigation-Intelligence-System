from rally_core.probability.resolver import (
    CandidatePlace,
    MissingWaypointContext,
    MissingWaypointResolver,
    WaypointAnchor,
)


def _ctx(target_km: float = 2.0, target_t: float = 180.0) -> MissingWaypointContext:
    return MissingWaypointContext(
        missing_text="X LR",
        previous=WaypointAnchor(id="prev", lat=-8.6700, lng=115.2200),
        next=WaypointAnchor(id="next", lat=-8.6710, lng=115.2400),
        target_distance_km=target_km,
        target_time_seconds=target_t,
        navigation_action="belok_kanan",
        landmark_type_hint="X",
        text_context="X LR Imam Bonjol",
    )


def test_high_confidence_candidate_in_corridor():
    resolver = MissingWaypointResolver()
    candidates = [
        CandidatePlace(
            id="c1",
            name="Simpang Imam Bonjol",
            lat=-8.6705,
            lng=115.2300,
            landmark_type="simpang_empat",
            source="curated",
            route_corridor_fit=0.95,
            turn_geometry_fit=0.9,
            name_context_match=0.9,
        ),
        CandidatePlace(
            id="c2",
            name="Pasar tak relevan",
            lat=-8.7000,
            lng=115.3000,
            landmark_type="pasar",
            source="osm",
            route_corridor_fit=0.2,
            turn_geometry_fit=0.3,
            name_context_match=0.1,
        ),
    ]
    result = resolver.evaluate(_ctx(), candidates)
    assert result.selected is not None
    assert result.selected.candidate.id == "c1"
    assert result.selected.confidence > 0.5


def test_empty_pool_unresolved():
    resolver = MissingWaypointResolver()
    result = resolver.evaluate(_ctx(), [])
    assert result.selected is None
    assert result.decision == "unresolved"
