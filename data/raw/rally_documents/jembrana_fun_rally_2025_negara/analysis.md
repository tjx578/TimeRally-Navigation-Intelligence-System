# Analysis - Jembrana Fun Rally 2025

## OCR Result

Dokumen berisi dua trayek:

- Trayek I: 40,6 km / 120 menit.
- Trayek II: 34,5 km / 120 menit.

Timing kedua trayek konsisten dengan total resmi pada soal.

## Waypoint Extraction

Total kandidat waypoint yang dimasukkan ke historical database: 65.

Breakdown:

| Type | Count |
|---|---:|
| POI | 26 |
| Road | 34 |
| Start point | 2 |
| Finish point | 2 |
| Intersection | 1 |

Match status:

| Status | Count |
|---|---:|
| `matched_from_jembrana_csv` | 7 |
| `partial_match_from_jembrana_csv` | 1 |
| `ocr_detected` | 39 |
| `needs_resolution` | 18 |

## Strong Matches From Jembrana CSV

| Raw waypoint | Matched candidate | Lat | Lng |
|---|---|---:|---:|
| SDN 1 Pergung | SD Negeri 1 Pergung | -8.3759249 | 114.6832685 |
| BR Bilukpoh Kangin | Balai Banjar Bilukpoh Kangin | -8.3786545 | 114.7010449 |
| BR Anyar Tembles | Balai Banjar Anyar Tembles | -8.3870921 | 114.7210833 |
| SDN 2 Yeh Kuning | SDN 2 Yehkuning | -8.3970616 | 114.6622863 |
| BR Munduk Asem | Balai Banjar Munduk Asem | -8.3613737 | 114.5602058 |
| BR Puana | Balai banjar puana | -8.3663074 | 114.5769386 |
| BR Sri Mandala | Balai Banjar Sri Mandala | -8.3642118 | 114.6354011 |

Partial match:

| Raw waypoint | Matched candidate | Reason |
|---|---|---|
| BR Anyar | Balai Dinas Banjar Anyar Tegal Badeng Barat | generic name, matched by route context Tegal Badeng Barat |

## Important Unresolved POI

Prioritas resolusi manual berikutnya:

- RS BALIMED
- Kantor Lurah Tegal Cangkring
- BR Sembung
- BR Celepud
- Kantor Kepala Desa Delod Berawah
- BR Delod Pangkung
- Kantor Kepala Desa Budeng
- SD 3 Loloan Timur
- SD 1 Loloan Barat
- RSU Negara
- BR Rening Cupel
- Kantor Kepala Desa Cupel
- Kantor Kepala Desa Tegal Badeng Barat
- Kantor Kepala Desa Tegal Badeng Timur
- Kantor Lurah Dauh Waru

## System Use

File waypoint candidate dipakai oleh place resolver sebagai historical memory.

Saat soal tahun berjalan menyebut salah satu lokasi di atas:

1. OCR mengekstrak token lokasi.
2. Resolver mencari di historical waypoint DB.
3. Kandidat dengan match lama diberi boost confidence.
4. UI menampilkan status kandidat: matched, partial, OCR-only, atau needs resolution.
5. Navigator memvalidasi titik di peta sebelum masuk roadbook.

Historical database:

```text
data/raw/historical_waypoints/jembrana/jembrana_fun_rally_2025_waypoint_candidates.csv
```
