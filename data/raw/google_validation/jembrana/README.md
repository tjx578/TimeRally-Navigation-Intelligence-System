# Jembrana Google Validation Staging

Dataset yang dianalisis:

```text
C:\Users\INTEL\Downloads\jembrana_maps_base_clean.csv
```

Status implementasi:
- layak dipakai sebagai staging place candidates,
- tidak dipakai langsung sebagai master offline POI,
- harus melalui field verification sebelum promosi ke `data/curated/places/jembrana/`.

Recommended generated files:

```text
jembrana_place_candidates_staging.csv
import_report.md
```

Cara generate:

```powershell
python .\tools\importers\jembrana_google_validation_csv.py --source "C:\Users\INTEL\Downloads\jembrana_maps_base_clean.csv" --output ".\data\raw\google_validation\jembrana\jembrana_place_candidates_staging.csv" --report ".\data\raw\google_validation\jembrana\import_report.md"
```
