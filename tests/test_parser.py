from rally_core import RallyParser


SAMPLE = """
Event: Pertamina Merah Putih Bali 2024
Trayek 1
Total Jarak 93.4 km
Total Waktu 270 menit
Start 07:30

Sub A: Menuju zero trip
Mode: Liaison Zero Trip
Jarak: 0 km
Waktu: 5 menit
BKR di POM SDN

Sub B: Zero trip ke KC Denpasar Barat
Mode: Average Speed
Jarak: 20.1 km
Waktu: 60 menit
JT di O Lapangan Renon
BKN di X LR Imam Bonjol
BKR di T br Suwung Kauh
KSM 2/DPS 11/PNT 0 finish
"""


def test_parse_basic_event_header():
    parser = RallyParser()
    result = parser.parse(SAMPLE)
    assert result.event.event_name.startswith("Pertamina Merah Putih")
    assert result.event.total_distance_km == 93.4
    assert result.event.total_time_minutes == 270
    assert result.event.rally_start_time == "07:30"
    assert result.event.trayek_name == "Trayek 1"


def test_parse_sub_trayeks_and_waypoints():
    parser = RallyParser()
    result = parser.parse(SAMPLE)
    labels = [s.label for s in result.event.sub_trayeks]
    assert labels == ["A", "B"]
    sub_b = result.event.sub_trayeks[1]
    assert sub_b.distance_km == 20.1
    assert sub_b.duration_minutes == 60
    assert sub_b.speed_mode == "average_speed"
    actions = [wp.action for wp in sub_b.waypoints]
    assert "jalan_terus" in actions
    assert "belok_kanan" in actions
    assert "belok_kiri" in actions


def test_parse_kmpal_marker():
    parser = RallyParser()
    result = parser.parse(SAMPLE)
    last_wp = result.event.sub_trayeks[1].waypoints[-1]
    assert last_wp.kmpal_marker is not None
    assert "KSM 2" in last_wp.kmpal_marker


def test_parse_case_sensitive_br_vs_banjar():
    parser = RallyParser()
    result = parser.parse(SAMPLE)
    sub_b = result.event.sub_trayeks[1]
    # Baris "BKR di T br Suwung Kauh" -> T = simpang_tiga, br = banjar.
    # Parser meng-compose landmark_type sekunder dan/atau menyimpan note.
    found = any(
        (wp.landmark_type and "banjar" in wp.landmark_type)
        or any("banjar" in note for note in wp.notes)
        for wp in sub_b.waypoints
    )
    assert found, "br lowercase harus diinterpretasi sebagai banjar"


def test_parse_liaison_zero_trip_not_counted_in_total():
    parser = RallyParser()
    result = parser.parse(SAMPLE)
    sub_a = result.event.sub_trayeks[0]
    assert sub_a.speed_mode == "liaison_zero_trip"
    assert sub_a.distance_counted_in_total is False
