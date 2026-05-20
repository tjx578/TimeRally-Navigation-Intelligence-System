# Web UI Implementation Plan

## Tujuan

Web UI menjadi pusat kerja analyst sebelum lomba dan pusat validasi rute. Tampilan pertama adalah workspace operasional, bukan halaman promosi.

## Layout Utama

```text
Topbar:
  event name, provider mode, validation status, export status

Left panel:
  input soal, upload OCR/PDF/XLSX/KML/GPX, parse action

Center:
  MapLibre map, route layers, waypoint, candidate, GPS trace

Right panel:
  validation, waypoint inspector, missing waypoint review

Bottom:
  roadbook table, ETA, distance, speed, status
```

## Fitur Prioritas MVP

1. Input soal rally dan parse awal.
2. Tabel waypoint hasil parse.
3. Resolve waypoint dari local POI.
4. Render waypoint di peta.
5. Route per leg lewat provider gateway.
6. Validasi jarak/waktu/chaining.
7. Missing waypoint review.
8. Export YAML, GPX, KML, GeoJSON.

## Fitur Championship

1. Per-sub-trayek compliance panel.
2. Provider comparison: Valhalla vs OSRM vs Google.
3. Confidence explanation untuk candidate.
4. Lock final route.
5. Generate offline package.
6. Print roadbook.
7. Replay GPS trace.

## Design Rules

- Dense but readable.
- No decorative landing page.
- Status must be visible at all times.
- Any inferred waypoint must be visually different from verified waypoint.
- Re-route must never reorder waypoint by default.

