"""Import spreadsheet lokasi ke curated place database dan map overlay.

Parser ini sengaja hanya memakai stdlib untuk membaca `.xlsx` sebagai ZIP/XML,
agar tidak bergantung pada openpyxl di mesin operator.
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INPUTS = [
    Path(r"D:\TIME RALLY\Spreadsheet\4ZDU3D7D.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\20F8ADAH.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\76JHJ0XB.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\D7RSP2LU.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\Daftar_Lokasi_Bersih__unik_.xlt"),
    Path(r"D:\TIME RALLY\Spreadsheet\ETAPE1 TRAYEK 1.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\F5265UR2.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\GQ3D8NMP.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\GY9B25DK.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\JQLVN4D2.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\LZDDFQWX.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\LZIT5G8W.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\M7E1PVJI.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\MKMOSR5C.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\QP4FQ600.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\RZVRQ2SY.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\S33E300D.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\TABEL HITUNG TIME RALLY.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\wisata.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\XLU5DC2A.xlsx"),
    Path(r"D:\TIME RALLY\Spreadsheet\ZDNRHRHP.xlsx"),
]

PLACES_YAML = REPO_ROOT / "data" / "curated" / "places" / "spreadsheet_locations.yaml"
PLACES_GEOJSON = (
    REPO_ROOT
    / "apps"
    / "web-map-console"
    / "public"
    / "data"
    / "locations"
    / "spreadsheet-locations.geojson"
)

NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

BALI_BOUNDS = {
    "min_lat": -9.2,
    "max_lat": -8.0,
    "min_lng": 114.3,
    "max_lng": 115.8,
}

SLUG_RE = re.compile(r"[^a-z0-9]+")


def normalize_target(target: str) -> str:
    clean = target.lstrip("/")
    return clean if clean.startswith("xl/") else f"xl/{clean}"


def column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    out = 0
    for letter in letters:
        out = out * 26 + ord(letter.upper()) - 64
    return out - 1


def read_shared_strings(zip_file: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("a:si", NS):
        values.append("".join(node.text or "" for node in item.iter(f"{{{NS['a']}}}t")))
    return values


def read_sheets(zip_file: ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zip_file.read("xl/workbook.xml"))
    rels = ET.fromstring(zip_file.read("xl/_rels/workbook.xml.rels"))
    targets = {
        rel.attrib["Id"]: normalize_target(rel.attrib["Target"])
        for rel in rels.findall("rel:Relationship", NS)
    }
    sheets = workbook.find("a:sheets", NS)
    if sheets is None:
        return []
    out: list[tuple[str, str]] = []
    for sheet in sheets.findall("a:sheet", NS):
        rel_id = sheet.attrib.get(f"{{{NS['r']}}}id")
        if rel_id and rel_id in targets:
            out.append((sheet.attrib["name"], targets[rel_id]))
    return out


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.iter(f"{{{NS['a']}}}t")).strip()

    value = cell.find("a:v", NS)
    if value is None:
        return ""

    raw = (value.text or "").strip()
    if cell_type == "s":
        try:
            return shared_strings[int(raw)].strip()
        except (IndexError, ValueError):
            return raw
    if cell_type == "b":
        return "TRUE" if raw == "1" else "FALSE"
    return raw


def read_sheet_rows(zip_file: ZipFile, sheet_path: str) -> list[list[str]]:
    shared_strings = read_shared_strings(zip_file)
    root = ET.fromstring(zip_file.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.findall(".//a:sheetData/a:row", NS):
        values: dict[int, str] = {}
        for cell in row.findall("a:c", NS):
            value = cell_value(cell, shared_strings)
            if value:
                values[column_index(cell.attrib.get("r", "A1"))] = value
        if values:
            width = max(values) + 1
            rows.append([values.get(index, "") for index in range(width)])
    return rows


def slug(value: str) -> str:
    return SLUG_RE.sub("_", value.lower()).strip("_")


def as_float(value: str) -> float | None:
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return None


def in_bali_bounds(lat: float, lng: float) -> bool:
    return (
        BALI_BOUNDS["min_lat"] <= lat <= BALI_BOUNDS["max_lat"]
        and BALI_BOUNDS["min_lng"] <= lng <= BALI_BOUNDS["max_lng"]
    )


def get(row: list[str], headers: dict[str, int], key: str) -> str:
    index = headers.get(key)
    if index is None or index >= len(row):
        return ""
    return str(row[index]).strip()


def compact_aliases(*values: str) -> list[str]:
    seen: set[str] = set()
    aliases: list[str] = []
    for value in values:
        clean = " ".join(str(value).strip().split())
        if not clean:
            continue
        norm = clean.lower()
        if norm in seen:
            continue
        seen.add(norm)
        aliases.append(clean)
    return aliases


def category_from_row(row: list[str], headers: dict[str, int]) -> str:
    raw = get(row, headers, "category") or get(row, headers, "type") or get(row, headers, "types")
    if not raw:
        return "unknown"
    first = raw.split(",")[0].strip()
    return slug(first) or "unknown"


def confidence_from_row(row: list[str], headers: dict[str, int]) -> float:
    rating = as_float(get(row, headers, "rating") or "")
    reviews = as_float(get(row, headers, "reviews") or "")
    score = 0.82
    if rating is not None and rating >= 4:
        score += 0.03
    if reviews is not None and reviews >= 10:
        score += 0.03
    if get(row, headers, "place_id"):
        score += 0.02
    return round(min(score, 0.92), 2)


def place_from_row(row: list[str], headers: dict[str, int], source_file: Path) -> dict | None:
    lat = as_float(get(row, headers, "latitude"))
    lng = as_float(get(row, headers, "longitude"))
    title = get(row, headers, "title")
    if lat is None or lng is None or not title:
        return None
    if not in_bali_bounds(lat, lng):
        return None

    city = get(row, headers, "city")
    state = get(row, headers, "state")
    address = get(row, headers, "address")
    aliases = compact_aliases(
        title,
        get(row, headers, "location_name"),
        address.split(",", 1)[0] if address else "",
    )
    return {
        "name": title,
        "aliases": aliases[1:],
        "lat": round(lat, 7),
        "lng": round(lng, 7),
        "category": category_from_row(row, headers),
        "region": city or state,
        "confidence": confidence_from_row(row, headers),
        "source": "spreadsheet_location_db",
        "source_file": source_file.name,
        "place_id": get(row, headers, "place_id") or None,
        "address": address or None,
    }


def dedupe_key(place: dict) -> str:
    place_id = place.get("place_id")
    if place_id:
        return f"place_id:{place_id}"
    return "coord:{:.5f}:{:.5f}:{}".format(
        place["lat"],
        place["lng"],
        slug(place["name"]),
    )


def merge_places(current: dict, incoming: dict) -> dict:
    aliases = compact_aliases(
        *current.get("aliases", []),
        *incoming.get("aliases", []),
        incoming.get("name", ""),
    )
    source_files = compact_aliases(
        str(current.get("source_file", "")),
        str(incoming.get("source_file", "")),
    )
    merged = {**current}
    merged["aliases"] = [alias for alias in aliases if alias.lower() != current["name"].lower()]
    merged["confidence"] = max(float(current["confidence"]), float(incoming["confidence"]))
    merged["source_file"] = ", ".join(source_files)
    if not merged.get("address") and incoming.get("address"):
        merged["address"] = incoming["address"]
    return merged


def load_places(inputs: list[Path]) -> tuple[list[dict], dict]:
    places_by_key: dict[str, dict] = {}
    stats = {
        "input_files": len(inputs),
        "xlsx_files_read": 0,
        "unsupported_files": [],
        "empty_or_non_location_sheets": 0,
        "rows_seen": 0,
        "rows_imported_before_dedupe": 0,
        "outside_bali_or_missing_coordinate": 0,
    }

    for path in inputs:
        if path.suffix.lower() != ".xlsx":
            stats["unsupported_files"].append(path.name)
            continue
        with ZipFile(path) as zip_file:
            stats["xlsx_files_read"] += 1
            for _, sheet_path in read_sheets(zip_file):
                rows = read_sheet_rows(zip_file, sheet_path)
                if not rows:
                    stats["empty_or_non_location_sheets"] += 1
                    continue
                headers = {slug(header): index for index, header in enumerate(rows[0]) if header}
                if "latitude" not in headers or "longitude" not in headers or "title" not in headers:
                    stats["empty_or_non_location_sheets"] += 1
                    continue
                for row in rows[1:]:
                    stats["rows_seen"] += 1
                    place = place_from_row(row, headers, path)
                    if place is None:
                        stats["outside_bali_or_missing_coordinate"] += 1
                        continue
                    stats["rows_imported_before_dedupe"] += 1
                    key = dedupe_key(place)
                    if key in places_by_key:
                        places_by_key[key] = merge_places(places_by_key[key], place)
                    else:
                        places_by_key[key] = place

    places = sorted(places_by_key.values(), key=lambda item: (item["region"], item["name"]))
    stats["unique_places"] = len(places)
    return places, stats


def write_yaml(places: list[dict], stats: dict) -> None:
    PLACES_YAML.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": {
            "generated_by": "tools/import_spreadsheet_locations.py",
            "governance_status": "needs_manual_review_before_final_rally_use",
            **stats,
        },
        "places": places,
    }
    text = yaml.safe_dump(payload, sort_keys=False, allow_unicode=False, width=120)
    PLACES_YAML.write_text(text, encoding="utf-8")


def write_geojson(places: list[dict], stats: dict) -> None:
    PLACES_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for place in places:
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": place["name"],
                    "category": place["category"],
                    "region": place["region"],
                    "confidence": place["confidence"],
                    "source_file": place["source_file"],
                    "address": place.get("address"),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [place["lng"], place["lat"]],
                },
            }
        )
    payload = {
        "type": "FeatureCollection",
        "metadata": {
            "generated_by": "tools/import_spreadsheet_locations.py",
            "governance_status": "needs_manual_review_before_final_rally_use",
            **stats,
        },
        "features": features,
    }
    PLACES_GEOJSON.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    places, stats = load_places(DEFAULT_INPUTS)
    write_yaml(places, stats)
    write_geojson(places, stats)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"wrote {PLACES_YAML}")
    print(f"wrote {PLACES_GEOJSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
