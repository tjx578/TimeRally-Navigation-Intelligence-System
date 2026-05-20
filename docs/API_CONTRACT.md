# API Contract

## Core Endpoints

### POST /v1/rally/parse

Input soal mentah.

Output:
- event,
- sub_trayeks,
- parsed_waypoints,
- unresolved tokens,
- warnings.

### POST /v1/rally/resolve

Resolve waypoint menjadi koordinat.

Output:
- verified coordinates,
- candidate list,
- confidence,
- source.

### POST /v1/rally/route

Route per leg sesuai urutan soal.

Output:
- route segments,
- distance,
- duration,
- provider comparison,
- polyline.

### POST /v1/rally/validate

Validasi absolute binding.

Output:
- distance compliance,
- time compliance,
- chaining compliance,
- violation report.

### POST /v1/rally/infer-missing-waypoints

Menjalankan probabilistic resolver.

Output:
- selected candidate,
- alternatives,
- confidence,
- explanation.

### POST /v1/rally/export

Export:
- YAML/EAML,
- GPX,
- KML,
- GeoJSON,
- roadbook,
- validation report.

## Provider Gateway Endpoints

```text
POST /v1/routing/route
POST /v1/routing/matrix
POST /v1/routing/nearest
POST /v1/routing/match
POST /v1/places/search
POST /v1/places/reverse
```

