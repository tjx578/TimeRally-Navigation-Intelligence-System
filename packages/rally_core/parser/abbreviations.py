"""Database singkatan rally NaviPRO.

Catatan:
- BR uppercase  -> arah Barat
- br lowercase  -> Banjar
- X             -> simpang empat
- T             -> simpang tiga
- O             -> bundaran
- POM           -> pom bensin/SPBU
- SDN/SMP/SMK   -> sekolah
- BKN/BKR/JT    -> belok kanan / belok kiri / jalan terus
- AKN/AKR       -> ambil kanan / ambil kiri
- BA            -> balik arah
- KMPAL         -> kilometer penanda dari titik nol trayek
- LR            -> lampu/rambu (sering muncul: X LR = simpang empat berlampu)

Database ini juga dipakai oleh knowledge_engine dan reasoning layer.
"""

from __future__ import annotations

# Aksi navigasi
NAV_ACTIONS: dict[str, str] = {
    "BKN": "belok_kanan",
    "BKNT": "belok_kanan_tajam",
    "BKR": "belok_kiri",
    "BKRT": "belok_kiri_tajam",
    "JT": "jalan_terus",
    "LRS": "lurus",
    "AKN": "ambil_kanan",
    "AKR": "ambil_kiri",
    "BA": "balik_arah",
    "U": "u_turn",
    "UJ": "ujung_jalan",
    "IJU": "ikuti_jalan_utama",
    "TKN": "tikung_kanan",
    "TKR": "tikung_kiri",
}

# Tipe landmark
LANDMARK_TYPES: dict[str, str] = {
    "O": "bundaran",
    "X": "simpang_empat",
    "T": "simpang_tiga",
    "POM": "spbu",
    "SPBU": "spbu",
    "JB": "jembatan",
    "JMB": "jembatan",
    "SDN": "sekolah_dasar",
    "SMP": "sekolah_menengah_pertama",
    "SMPN": "sekolah_menengah_pertama",
    "SMA": "sekolah_menengah_atas",
    "SMUN": "sekolah_menengah_atas",
    "SMK": "sekolah_menengah_kejuruan",
    "KC": "kantor_camat",
    "KL": "kantor_lurah",
    "KKD": "kantor_kepala_desa",
    "JEMB": "jembatan",
    "BPBD": "kantor_bpbd",
    "PASAR": "pasar",
    "PURA": "pura",
    "BANJAR": "banjar",
    "ZP": "zero_point",
    "FP": "finish_point",
    "PAD": "pos_waktu_detik",
    "PAM": "pos_waktu_menit",
    "PAR": "pos_rute",
    "TC": "time_control",
    "KA": "lintasan_kereta_api",
    "DKT": "daerah_kecepatan_terbatas",
}

# Tipe landmark yang case-sensitive (BR vs br)
CASE_SENSITIVE_TOKENS: dict[str, dict[str, str]] = {
    "BR": {"type": "arah", "value": "barat"},
    "br": {"type": "landmark", "value": "banjar"},
    "TM": {"type": "arah", "value": "timur"},
    "tm": {"type": "landmark", "value": "taman"},
    "UT": {"type": "arah", "value": "utara"},
    "SL": {"type": "arah", "value": "selatan"},
}

# Modifier landmark (LR = lampu/rambu, ZB = zebra cross)
LANDMARK_MODIFIERS: dict[str, str] = {
    "LR": "berlampu",
    "ZB": "zebra_cross",
    "ST": "stop",
    "YL": "yield",
    "H": "hati_hati",
}

# Mode kecepatan
SPEED_MODE_TOKENS: dict[str, str] = {
    "KR": "average_speed",
    "KRT": "average_speed",
    "TD": "fixed_second",
    "TS": "fixed_second",
    "SS": "remaining_distance",
    "LIA": "liaison_zero_trip",
    "ZT": "liaison_zero_trip",
}

# Relasi spasial
RELATION_PREPS: dict[str, str] = {
    "di": "at",
    "sblm": "before",
    "sebelum": "before",
    "stlh": "after",
    "setelah": "after",
    "psd": "passed",
    "passed": "passed",
}


def is_nav_action(token: str) -> bool:
    return token.upper() in NAV_ACTIONS


def normalize_landmark_type(token: str) -> str | None:
    """Mengembalikan tipe landmark canonical jika token dikenal."""
    if token in CASE_SENSITIVE_TOKENS:
        info = CASE_SENSITIVE_TOKENS[token]
        if info["type"] == "landmark":
            return info["value"]
    if token.upper() in LANDMARK_TYPES:
        return LANDMARK_TYPES[token.upper()]
    return None


def normalize_action(token: str) -> str | None:
    return NAV_ACTIONS.get(token.upper())


def is_landmark_modifier(token: str) -> bool:
    return token.upper() in LANDMARK_MODIFIERS


def get_direction(token: str) -> str | None:
    """Khusus BR/TM/UT/SL uppercase - arah mata angin."""
    info = CASE_SENSITIVE_TOKENS.get(token)
    if info and info["type"] == "arah":
        return info["value"]
    return None
