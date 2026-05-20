# Missing Waypoint Probability

Modul ini menjawab kasus penting: waypoint di soal tidak ditemukan, tetapi waypoint sebelum dan sesudahnya ditemukan.

## Problem

```text
A ditemukan -> B tidak ditemukan -> C ditemukan
```

Sistem tidak boleh menebak bebas. Sistem harus mencari kandidat B yang paling mungkin berdasarkan constraint rally.

## Candidate Sources

Kandidat B diambil dari:
- local POI database,
- KMPAL database,
- OSM intersections,
- Nominatim search,
- route graph nodes,
- Google Places online,
- manual marshal hints.

## Scoring Formula

Default scoring:

```text
score =
  0.35 * time_distance_fit
+ 0.20 * landmark_type_fit
+ 0.15 * turn_geometry_fit
+ 0.15 * route_corridor_fit
+ 0.10 * name_context_fit
+ 0.05 * source_quality
```

## Feature Explanation

### time_distance_fit

Apakah `A -> B -> C` membuat jarak/waktu mendekati target soal.

### landmark_type_fit

Apakah B sesuai jenis waypoint:
- `O` harus bundaran atau roundabout.
- `X` harus intersection/crossroad.
- `T` harus T-junction.
- `br` harus banjar/community center/village hall.
- `POM` harus gas station.

### turn_geometry_fit

Apakah bentuk jalan memungkinkan instruksi:
- BKN,
- BKR,
- JT,
- BA,
- AKR,
- AKN.

### route_corridor_fit

Apakah kandidat berada di koridor realistis antara A dan C.

### name_context_fit

Apakah nama area cocok dengan teks sekitar.

### source_quality

Prioritas:
1. verified local survey,
2. KMPAL verified,
3. curated POI,
4. OSM,
5. Google online,
6. inferred graph node.

## Output Contract

```yaml
missing_waypoint:
  original_text: "X LR"
  status: inferred_high_confidence
  selected_candidate:
    name: "Simpang Empat Jl. Raya Kamasan"
    lat: -8.123456
    lng: 115.123456
    confidence: 0.87
    source: probabilistic_route_constraint
    reason:
      - "distance deviation 1.4%"
      - "landmark type matches simpang empat"
      - "turn geometry supports BKR"
      - "inside route corridor from WP previous to WP next"
  alternatives:
    - name: "Simpang Pasar Kamasan"
      confidence: 0.72
```

## Decision Rule

```text
confidence >= 0.85 -> auto select but mark inferred
0.70 <= confidence < 0.85 -> ask human confirmation
confidence < 0.70 -> unresolved
```

## Championship Rule

Inferensi tidak boleh disamakan dengan data verified. Output final harus membawa status dan confidence.

