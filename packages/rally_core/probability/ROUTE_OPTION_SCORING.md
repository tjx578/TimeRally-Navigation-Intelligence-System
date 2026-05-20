# Route Option Scoring

Skoring opsi rute digunakan saat waypoint hilang atau saat beberapa provider memberi rute berbeda.

## Default Formula

```text
score =
  0.35 * distance_time_fit
+ 0.20 * landmark_fit
+ 0.15 * turn_geometry_fit
+ 0.15 * route_corridor_fit
+ 0.10 * source_quality
+ 0.05 * operator_preference
```

## Distance Time Fit

Mengukur seberapa dekat kandidat terhadap target sub-trayek.

## Landmark Fit

Mengukur kecocokan kandidat dengan teks soal:

- O = bundaran.
- X = simpang empat.
- T = simpang tiga.
- br = banjar/community center.
- POM = SPBU.
- SDN/SMP/SMK = sekolah.

## Turn Geometry Fit

Mengukur apakah instruksi seperti BKN/BKR/JT/BA bisa dilakukan secara geometris.

## Route Corridor Fit

Mengukur apakah kandidat berada di koridor logis antara waypoint sebelum dan sesudahnya.

## Source Quality

Prioritas:

1. field verified,
2. curated local POI,
3. KMPAL verified,
4. OSM/Nominatim,
5. Google online validation,
6. inferred graph node.

## Decision

```text
>= 0.85 -> recommended
0.70-0.84 -> review
< 0.70 -> unresolved
```

