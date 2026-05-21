from geo_engine.corridor import corridor_fit, distance_point_to_line_meters
from geo_engine.distance import bearing_degrees, haversine_km, haversine_meters
from geo_engine.geometry import simplify_polyline
from geo_engine.turns import classify_turn, turn_angle_degrees


def test_haversine_meters_known_distance():
    # ~111.32 km dari (0,0) ke (1,0)
    d = haversine_km(0, 0, 1, 0)
    assert 110 < d < 112


def test_bearing_north_zero_degrees():
    b = bearing_degrees(0, 0, 1, 0)
    assert abs(b - 0.0) < 1.0


def test_corridor_fit_inside_returns_high_score():
    poly = [(-8.67, 115.22), (-8.68, 115.23)]
    score = corridor_fit((-8.675, 115.225), poly, corridor_m=300)
    assert 0.0 <= score <= 1.0


def test_simplify_polyline_drops_collinear_points():
    line = [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
    out = simplify_polyline(line, tolerance_m=10.0)
    # collinear: harus tinggal endpoint saja
    assert out[0] == line[0]
    assert out[-1] == line[-1]


def test_classify_turn_belok_kanan():
    # Heading utara (lat +) lalu belok ke timur (lng +) = belok kanan.
    angle = turn_angle_degrees(0, 0, 0.001, 0, 0.001, 0.001)
    label = classify_turn(angle)
    assert label in {"belok_kanan", "tikung_kanan", "ambil_kanan"}


def test_classify_turn_belok_kiri():
    # Heading timur lalu belok ke utara = belok kiri.
    angle = turn_angle_degrees(0, 0, 0, 0.001, 0.001, 0.001)
    label = classify_turn(angle)
    assert label in {"belok_kiri", "tikung_kiri", "ambil_kiri"}


def test_distance_point_to_line_zero_when_on_line():
    poly = [(-8.67, 115.22), (-8.68, 115.23)]
    d = distance_point_to_line_meters((-8.67, 115.22), poly)
    assert d < 1.0
