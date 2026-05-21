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


def test_parse_legacy_markdown_letter_headers_and_fixed_minute():
    raw = """
### **A. Menuju Zero Trip**
* **Waktu:** 5 menit
* **Jarak:** Tidak ditentukan (berbasis waktu)
* **Titik Navigasi:**
  1. Start, Jl. Mulawarman
  2. BKN di X LR

B. Zero Trip:
Waktu: 60 menit
Jarak: 20,10 km
Mode Kecepatan: Tetap Menit
1. BKR di KSM 2
2. JT di DPS 11
"""
    result = RallyParser().parse(raw)
    assert [sub.label for sub in result.event.sub_trayeks] == ["A", "B"]
    sub_a, sub_b = result.event.sub_trayeks
    assert sub_a.distance_km is None
    assert sub_a.distance_counted_in_total is False
    assert sub_b.speed_mode == "fixed_minute"
    assert sub_b.distance_km == 20.1
    assert sub_b.waypoints[0].kmpal_marker == "KSM 2"


def test_speed_kmh_is_not_misread_as_distance():
    raw = """
Sub B: Zero trip ke finish
Mode: Average Speed
Waktu: 38 menit
Kecepatan: 19,67 km/jam
BKR di X Penarungan
"""
    result = RallyParser().parse(raw)
    sub_b = result.event.sub_trayeks[0]
    assert sub_b.distance_km is None
    assert sub_b.duration_minutes == 38


def test_parse_free_time_mode_from_santai():
    raw = """
Sub D: Santai sambil melihat objek
Selama 45 menit
Arah Ubud/Gianyar - IJU - BR. Kedewatan
"""
    result = RallyParser().parse(raw)
    assert result.event.sub_trayeks[0].speed_mode == "free_time"


def test_parse_dash_delimited_time_rally_waypoints():
    raw = """
Sub A:
START - BKR - BKR di LR - RS BALIMED - Langsung menuju SDN 1 Pergung - BKR, Jalan Ketut Gelot - BKR di T Kantor Lurah Tegal Cangkring - BKN - BR.Bilukpoh Kangin di kanan - BR. Sembung di kanan - Jalan Kartini - Jalan Rama - BKN, JL Yudistira - BKR - IJU - BKR, Jalan Sahadewa - Jalan Anggrek - BR Anyar Tembles, dengan jarak, 15,8km
"""
    result = RallyParser().parse(raw)
    sub = result.event.sub_trayeks[0]

    assert sub.label == "A"
    assert sub.title == "Sub A"
    assert sub.distance_km == 15.8
    assert [wp.raw_text for wp in sub.waypoints] == [
        "START",
        "BKR",
        "BKR di LR",
        "RS BALIMED",
        "Langsung menuju SDN 1 Pergung",
        "BKR, Jalan Ketut Gelot",
        "BKR di T Kantor Lurah Tegal Cangkring",
        "BKN",
        "BR.Bilukpoh Kangin di kanan",
        "BR. Sembung di kanan",
        "Jalan Kartini",
        "Jalan Rama",
        "BKN, JL Yudistira",
        "BKR",
        "IJU",
        "BKR, Jalan Sahadewa",
        "Jalan Anggrek",
        "BR Anyar Tembles",
    ]

    assert sub.waypoints[5].action == "belok_kiri"
    assert sub.waypoints[3].landmark_type == "rumah_sakit"
    assert sub.waypoints[3].landmark_name == "BALIMED"
    assert sub.waypoints[4].relation == "toward"
    assert sub.waypoints[4].landmark_type == "sekolah_dasar"
    assert sub.waypoints[4].landmark_name == "1 Pergung"
    assert sub.waypoints[5].landmark_name == "Jalan Ketut Gelot"
    assert sub.waypoints[6].landmark_type == "simpang_tiga"
    assert sub.waypoints[6].landmark_name == "Kantor Lurah Tegal Cangkring"
    assert sub.waypoints[8].landmark_type == "banjar"
    assert sub.waypoints[8].landmark_name == "Bilukpoh Kangin"
    assert sub.waypoints[12].action == "belok_kanan"
    assert sub.waypoints[12].landmark_name == "Jalan Yudistira"
    assert sub.waypoints[-1].landmark_type == "banjar"
    assert sub.waypoints[-1].landmark_name == "Anyar Tembles"


def test_parse_inline_sub_header_route_sequence():
    raw = "Sub B: START - BKN - IJU - BR. Kedewatan, dengan jarak, 2,5km"

    result = RallyParser().parse(raw)
    sub = result.event.sub_trayeks[0]

    assert sub.title == "Sub B"
    assert sub.distance_km == 2.5
    assert [wp.raw_text for wp in sub.waypoints] == ["START", "BKN", "IJU", "BR. Kedewatan"]


def test_parse_numbered_sub_labels_and_start_finish_chaining():
    raw = """
Sub 1.1:
START - BKR - BKR di LR - RS BALIMED - Langsung menuju SDN 1 Pergung - BKR, Jalan Ketut Gelot - BKR di T Kantor Lurah Tegal Cangkring - BKN - BR.Bilukpoh Kangin di kanan - Jalan Kartini - BR Anyar Tembles, dengan jarak, 15,8km

Sub 1.2:
BKR - Jalan Rama - BKN, JL Yudistira - BR Sembung - Finish di Kantor Desa Pergung, jarak 4,2km
"""

    result = RallyParser().parse(raw)
    sub_11, sub_12 = result.event.sub_trayeks

    assert [sub.label for sub in result.event.sub_trayeks] == ["1.1", "1.2"]
    assert sub_11.title == "Sub 1.1"
    assert sub_11.distance_km == 15.8
    assert sub_11.start_status == "missing_location"
    assert sub_11.start_raw_text == "START"
    assert sub_11.needs_user_start is True
    assert sub_11.finish_status == "inferred_last_waypoint"
    assert sub_11.finish_raw_text == "BR Anyar Tembles"
    assert sub_11.needs_user_finish is False

    assert sub_12.title == "Sub 1.2"
    assert sub_12.distance_km == 4.2
    assert sub_12.start_status == "inherited"
    assert sub_12.start_raw_text == "BR Anyar Tembles"
    assert sub_12.needs_user_start is False
    assert sub_12.finish_status == "explicit"
    assert sub_12.finish_raw_text == "Finish di Kantor Desa Pergung"
    assert sub_12.needs_user_finish is False
    assert sub_12.waypoints[-1].relation == "at"
    assert sub_12.waypoints[-1].landmark_name == "Kantor Desa Pergung"

    assert any("1.1: titik START belum memiliki lokasi" in warning for warning in result.warnings)
    assert any("1.2: START diwarisi dari FINISH sub sebelumnya" in warning for warning in result.warnings)
    assert any(token.reason == "start_location_required" for token in result.unresolved_tokens)


def test_parse_trayek_dotted_label_without_confusing_header_trayek():
    raw = """
Event: Trial
Trayek 1

Trayek 2.3: Start di Lapangan Desa - BKN - Finish di Kantor Desa
"""

    result = RallyParser().parse(raw)
    assert result.event.trayek_name == "Trayek 1"
    assert [sub.label for sub in result.event.sub_trayeks] == ["2.3"]
    sub = result.event.sub_trayeks[0]
    assert sub.start_status == "explicit"
    assert sub.finish_status == "explicit"
    assert sub.waypoints[0].landmark_name == "Lapangan Desa"
    assert sub.waypoints[-1].landmark_name == "Kantor Desa"
