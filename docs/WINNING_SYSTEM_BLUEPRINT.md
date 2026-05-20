# Winning System Blueprint

Tujuan sistem adalah memenangkan lomba time rally dengan mengurangi error navigasi, error waktu, dan error interpretasi soal.

## Tiga Pilar Menang

### 1. Route Correctness

Sistem harus memastikan rute mengikuti soal, bukan sekadar rute tercepat.

Quality gate:
- semua waypoint resolved,
- urutan waypoint tetap,
- tidak ada illegal shortcut,
- chaining sub-trayek valid,
- route realism normal.

### 2. Time Precision

Sistem harus memberi navigator waktu yang presisi.

Quality gate:
- formula waktu sesuai mode,
- ETA kumulatif tersedia,
- warning jika jarak/waktu tidak binding,
- toleransi detik untuk mode Tetap Detik.

### 3. Ambiguity Control

Soal rally sering ambigu. Sistem harus menangani ambiguitas secara eksplisit.

Quality gate:
- kandidat waypoint diberi confidence,
- alasan pemilihan kandidat ditulis,
- alternatif tetap disimpan,
- human confirmation untuk confidence sedang.

## Race-Day Workflow

```text
1. Import soal/OCR.
2. Parse sub-trayek.
3. Resolve waypoint local-first.
4. Run missing waypoint probability.
5. Route with Valhalla/OSRM.
6. Validate with Google online if available.
7. Generate roadbook.
8. Export offline package.
9. Sync to field mobile.
10. During race: track, warn, replay.
```

## Operator Roles

### Navigator

Membaca roadbook, ETA, dan turn cues.

### Analyst

Mengecek ambiguous waypoint dan compliance.

### Map Engineer

Menyiapkan OSM extract, tile, dan routing graph.

### Marshal/Surveyor

Memvalidasi waypoint lapangan dan KMPAL.

## Output Siap Lomba

Sistem dianggap siap jika menghasilkan:

```text
event.yaml
roadbook.pdf
route.gpx
route.kml
route.geojson
offline-map.pmtiles
validation-report.md
championship-score.json
candidate-review.md
```

