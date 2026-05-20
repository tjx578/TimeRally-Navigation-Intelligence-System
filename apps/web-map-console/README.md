# Web Map Console

Console untuk analyst dan navigator.

## Fungsi

- Menampilkan route di MapLibre.
- Edit dan lock waypoint.
- Review candidate missing waypoint.
- Menampilkan warning distance/time/chaining.
- Export YAML, GPX, KML, GeoJSON, roadbook.
- Switch provider result: Valhalla, OSRM, GraphHopper, Google.

## Feature Areas

```text
src/features/rally-map
src/features/roadbook
src/features/validation
```

## UI Prinsip Lomba

UI harus cepat dibaca, padat, dan tidak seperti landing page. Prioritasnya:

- status waypoint,
- ETA,
- deviasi,
- confidence,
- next turn.
