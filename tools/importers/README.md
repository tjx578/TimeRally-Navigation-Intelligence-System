# Importers

Importer memindahkan legacy data ke struktur baru tanpa merusak file asli.

## Import Targets

- Markdown SOP -> `data/curated/rally_rules`
- JSON/CSV place DB -> `data/curated/places`
- YAML examples -> `data/fixtures/rally_cases`
- GPX/KML -> `data/fixtures/rally_cases`
- Python processors -> `packages/rally_core`

## Rules

Importer harus:
- preserve original file,
- write normalized output,
- create import report,
- detect duplicates,
- validate schema.

## Available Importers

### `jembrana_google_validation_csv.py`

Mengubah `jembrana_maps_base_clean.csv` menjadi staging candidates dengan label restricted-use:

```powershell
python .\tools\importers\jembrana_google_validation_csv.py --source "C:\Users\INTEL\Downloads\jembrana_maps_base_clean.csv" --output ".\data\raw\google_validation\jembrana\jembrana_place_candidates_staging.csv" --report ".\data\raw\google_validation\jembrana\import_report.md"
```

Output ini dipakai untuk resolver staging dan validasi online, bukan untuk master offline POI permanen.
