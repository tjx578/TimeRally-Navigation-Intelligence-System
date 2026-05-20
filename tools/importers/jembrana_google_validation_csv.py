from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


STAGING_FIELDS = [
    "source_row_no",
    "name",
    "category_group",
    "category",
    "district",
    "village",
    "lat",
    "lng",
    "google_place_id",
    "google_maps_url",
    "query_source",
    "source_files",
    "duplicate_count_removed",
    "quality_note",
    "source",
    "source_license",
    "verification_status",
    "allowed_use",
]


@dataclass(frozen=True)
class ImportProfile:
    rows: int
    unique_place_ids: int
    blank_coordinates: int
    outside_bali_bounds: int
    duplicate_name_count: int
    with_google_maps_url: int
    with_thumbnail_url: int
    with_reviews_url: int
    duplicate_count_removed_rows: int
    blank_road_rows: int
    blank_rating_rows: int


def normalize_name(value: str) -> str:
    return " ".join(value.lower().strip().split())


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def parse_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def inside_bali_bounds(lat: float | None, lng: float | None) -> bool:
    if lat is None or lng is None:
        return False
    return -8.9 <= lat <= -8.0 and 114.3 <= lng <= 115.8


def read_rows(source: Path) -> list[dict[str, str]]:
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def profile_rows(rows: list[dict[str, str]]) -> ImportProfile:
    place_ids = {row.get("place_id", "").strip() for row in rows if not is_blank(row.get("place_id"))}
    names = Counter(normalize_name(row.get("nama_tempat", "")) for row in rows if not is_blank(row.get("nama_tempat")))
    duplicate_names = sum(1 for count in names.values() if count > 1)

    blank_coordinates = 0
    outside_bounds = 0
    for row in rows:
        lat = parse_float(row.get("latitude", ""))
        lng = parse_float(row.get("longitude", ""))
        if lat is None or lng is None:
            blank_coordinates += 1
        elif not inside_bali_bounds(lat, lng):
            outside_bounds += 1

    return ImportProfile(
        rows=len(rows),
        unique_place_ids=len(place_ids),
        blank_coordinates=blank_coordinates,
        outside_bali_bounds=outside_bounds,
        duplicate_name_count=duplicate_names,
        with_google_maps_url=sum(1 for row in rows if not is_blank(row.get("google_maps_url"))),
        with_thumbnail_url=sum(1 for row in rows if not is_blank(row.get("thumbnail_url"))),
        with_reviews_url=sum(1 for row in rows if not is_blank(row.get("reviews_url"))),
        duplicate_count_removed_rows=sum(
            1
            for row in rows
            if (parse_float(row.get("duplicate_count_removed", "")) or 0) > 0
        ),
        blank_road_rows=sum(1 for row in rows if is_blank(row.get("jalan"))),
        blank_rating_rows=sum(1 for row in rows if is_blank(row.get("rating"))),
    )


def to_staging_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "source_row_no": row.get("no", "").strip(),
        "name": row.get("nama_tempat", "").strip(),
        "category_group": row.get("kelompok_kategori", "").strip(),
        "category": row.get("kategori", "").strip(),
        "district": row.get("kecamatan", "").strip(),
        "village": row.get("desa_kelurahan", "").strip(),
        "lat": row.get("latitude", "").strip(),
        "lng": row.get("longitude", "").strip(),
        "google_place_id": row.get("place_id", "").strip(),
        "google_maps_url": row.get("google_maps_url", "").strip(),
        "query_source": row.get("query_sumber", "").strip(),
        "source_files": row.get("source_files", "").strip(),
        "duplicate_count_removed": row.get("duplicate_count_removed", "").strip(),
        "quality_note": row.get("quality_note", "").strip(),
        "source": "google_validation_import",
        "source_license": "restricted_google_derived",
        "verification_status": "needs_field_verification",
        "allowed_use": "resolver_staging_google_validation_only",
    }


def write_staging_csv(rows: list[dict[str, str]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STAGING_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(to_staging_row(row))


def write_report(profile: ImportProfile, rows: list[dict[str, str]], report: Path) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    by_district = Counter(row.get("kecamatan", "").strip() for row in rows)
    by_group = Counter(row.get("kelompok_kategori", "").strip() for row in rows)
    duplicate_names = [
        (name, count)
        for name, count in Counter(normalize_name(row.get("nama_tempat", "")) for row in rows).items()
        if count > 1
    ]

    lines = [
        "# Jembrana Google Validation Import Report",
        "",
        "## Profile",
        "",
        f"- Rows: {profile.rows}",
        f"- Unique place IDs: {profile.unique_place_ids}",
        f"- Blank coordinates: {profile.blank_coordinates}",
        f"- Outside Bali bounds: {profile.outside_bali_bounds}",
        f"- Duplicate normalized names: {profile.duplicate_name_count}",
        f"- Rows with Google Maps URL: {profile.with_google_maps_url}",
        f"- Rows with thumbnail URL: {profile.with_thumbnail_url}",
        f"- Rows with reviews URL: {profile.with_reviews_url}",
        f"- Rows with duplicate_count_removed > 0: {profile.duplicate_count_removed_rows}",
        f"- Blank road rows: {profile.blank_road_rows}",
        f"- Blank rating rows: {profile.blank_rating_rows}",
        "",
        "## By District",
        "",
    ]
    lines.extend(f"- {name}: {count}" for name, count in by_district.most_common())
    lines.extend(["", "## By Category Group", ""])
    lines.extend(f"- {name}: {count}" for name, count in by_group.most_common())
    lines.extend(["", "## Duplicate Normalized Names", ""])
    if duplicate_names:
        lines.extend(f"- {name}: {count}" for name, count in duplicate_names)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Governance",
            "",
            "Generated rows are staging candidates only.",
            "Do not promote them to curated offline POI until field verification or a storage-safe source confirms the place.",
        ]
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_profile(profile: ImportProfile) -> None:
    print(f"rows={profile.rows}")
    print(f"unique_place_ids={profile.unique_place_ids}")
    print(f"blank_coordinates={profile.blank_coordinates}")
    print(f"outside_bali_bounds={profile.outside_bali_bounds}")
    print(f"duplicate_normalized_names={profile.duplicate_name_count}")
    print(f"with_google_maps_url={profile.with_google_maps_url}")
    print(f"with_thumbnail_url={profile.with_thumbnail_url}")
    print(f"with_reviews_url={profile.with_reviews_url}")
    print(f"duplicate_count_removed_rows={profile.duplicate_count_removed_rows}")
    print(f"blank_road_rows={profile.blank_road_rows}")
    print(f"blank_rating_rows={profile.blank_rating_rows}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Jembrana Google validation CSV into restricted-use staging format.")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    rows = read_rows(args.source)
    profile = profile_rows(rows)
    print_profile(profile)

    if args.output:
        write_staging_csv(rows, args.output)
    if args.report:
        write_report(profile, rows, args.report)


if __name__ == "__main__":
    main()
