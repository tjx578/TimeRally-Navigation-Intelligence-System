# Rally Reasoning Pipeline

Pipeline ini adalah logika berpikir sistem saat memahami soal rally.

## Step 0: Intake

Input bisa berupa:
- teks soal,
- OCR dari gambar,
- PDF,
- spreadsheet,
- GPX/KML route,
- data manual marshal.

Output:
- normalized text,
- source metadata,
- confidence OCR,
- file evidence.

## Step 1: Structure Detection

Sistem mencari:
- nama event,
- trayek,
- sub-trayek,
- total jarak,
- total waktu,
- mode kecepatan,
- start/finish,
- tulip/gambar,
- instruksi per waypoint.

## Step 2: Abbreviation and Context Parsing

Contoh:

```text
BKN di O
```

Diurai menjadi:

```yaml
action: belok_kanan
landmark_type: bundaran
relation: at
```

Context rule:
- `BR` uppercase = Barat.
- `br` lowercase = Banjar.
- `X` = simpang empat.
- `T` = simpang tiga.
- `O` = bundaran.
- `SDN/SMP/SMK` = school landmark.

## Step 3: Waypoint Graph

Soal diubah menjadi graph berurutan:

```text
WP001 -> WP002 -> WP003 -> ... -> FINISH
```

Graph tidak boleh dioptimasi seperti salesman problem. Rally mengikuti urutan soal.

## Step 4: Place Resolution

Setiap waypoint diberi status:

```text
verified_local
verified_kmpal
verified_osm
verified_google_online
inferred_high_confidence
inferred_low_confidence
unresolved
```

## Step 5: Routing Per Leg

Setiap leg dihitung:

```text
WP001 -> WP002
WP002 -> WP003
WP003 -> WP004
```

Output leg:
- distance_m,
- duration_s,
- polyline,
- turn instruction,
- route_provider,
- route_confidence.

## Step 6: Absolute Binding Validation

Validasi:

```text
sum(distance_leg) == distance_soal
sum(duration_leg) == waktu_soal
finish(sub_n) == start(sub_n+1)
```

Jika deviasi besar, sistem masuk mode correction/probability.

## Step 7: Missing Waypoint Probability

Jika waypoint hilang, sistem mencari kandidat yang membuat:

```text
A -> missing_candidate -> C
```

paling sesuai waktu, jarak, arah, tipe landmark, dan koridor route.

## Step 8: Championship Scoring

Score dihitung dari:
- distance compliance,
- time formula accuracy,
- waypoint chaining,
- coordinate precision,
- knowledge hit rate,
- Google/OSM route validation,
- output completeness.

## Step 9: Output

Output final:
- YAML/EAML,
- table time rally,
- Google Maps link,
- offline route package,
- GPX/KML/GeoJSON,
- warning report,
- candidate explanation.

