# Excel POI Source Files Assessment

Reviewed files:

```text
C:\Users\INTEL\Downloads\Excel\55I5CHTK.xlsx
C:\Users\INTEL\Downloads\Excel\XEHWHPS2.xlsx
C:\Users\INTEL\Downloads\Excel\NPI4WJKR.xlsx
C:\Users\INTEL\Downloads\Excel\27V9U5AJ.xlsx
C:\Users\INTEL\Downloads\Excel\LZJ0F447.xlsx
C:\Users\INTEL\Downloads\Excel\6N5ZBM1B.xlsx
C:\Users\INTEL\Downloads\Excel\4NNMEREG.xlsx
```

## Verdict

File Excel ini adalah **raw Google Places export source** untuk kandidat lokasi. Untuk sistem Time Rally, nilai utamanya adalah sebagai bahan asal dari database lokasi Jembrana.

Kesimpulan paling penting:

- Total raw rows: 626.
- Unique `place_id`: 583.
- Rows dengan koordinat kosong: 0.
- Unique lokasi Jembrana: 239.
- Semua 239 lokasi Jembrana ini sudah tercakup di `jembrana_maps_base_clean.csv`.
- Jadi `jembrana_maps_base_clean.csv` adalah bentuk yang lebih siap pakai dibanding Excel raw.

## File Breakdown

| File | Query / Tema | Raw Rows | Jembrana Rows | Catatan |
|---|---|---:|---:|---|
| `6N5ZBM1B.xlsx` | `balai banjar` | 296 | 144 | Sumber paling penting untuk rally. |
| `27V9U5AJ.xlsx` | `sdn` | 102 | 50 | Berguna untuk waypoint sekolah dasar. |
| `55I5CHTK.xlsx` | `SMPN` | 60 | 28 | Campuran Jembrana dan luar daerah. |
| `XEHWHPS2.xlsx` | `sekolah menengah pertama` | 27 | 21 | Overlap kuat dengan file SMPN. |
| `NPI4WJKR.xlsx` | `sekolah menengah pertama` | 21 | 21 | Subset Jembrana yang bersih. |
| `LZJ0F447.xlsx` | `kantor kepala desa` | 30 | 14 | Berguna untuk kantor desa/perbekel. |
| `4NNMEREG.xlsx` | `bundaran` | 90 | 0 | Mayoritas luar Jembrana; jangan masuk DB Jembrana. |

## Aggregated Data Quality

| Check | Result |
|---|---:|
| Total raw records | 626 |
| Unique `place_id` | 583 |
| Duplicate `place_id` rows | 43 |
| Duplicate normalized title names | 38 |
| Missing latitude/longitude | 0 |
| Rows outside rough Jembrana bounds | 277 |
| Rows outside Bali bounds | 123 |
| Place IDs already in `jembrana_maps_base_clean.csv` | 239 |
| Place IDs not in clean CSV | 344 |

Catatan: 344 place IDs yang tidak ada di clean CSV mayoritas adalah data luar Jembrana, bukan tambahan penting untuk DB Jembrana.

## Jembrana-Only Profile

| Check | Result |
|---|---:|
| Jembrana raw rows | 278 |
| Jembrana unique `place_id` | 239 |
| Jembrana duplicate rows | 39 |

Jembrana rows by query:

| Query | Rows |
|---|---:|
| `balai banjar` | 144 |
| `sdn` | 50 |
| `sekolah menengah pertama` | 42 |
| `SMPN` | 28 |
| `kantor kepala desa` | 14 |

Jembrana rows by type:

| Type | Rows |
|---|---:|
| Community center | 109 |
| Middle school | 63 |
| Elementary school | 37 |
| Village hall | 13 |
| Government office | 11 |
| Educational institution | 5 |

## System Fit

### Bisa Dipakai Untuk

- Historical waypoint resolver.
- Kandidat lokasi saat OCR soal menemukan `BR`, `SDN`, `SMPN`, `Kantor Kepala Desa`, atau `Perbekel`.
- Cross-check kandidat dari soal lama ke soal baru.
- Menambah alias dan kategori ke `jembrana_maps_base_clean.csv`.

### Jangan Dipakai Langsung Untuk

- Master offline POI permanen.
- Offline routing graph.
- Tile cache.
- Data Google content seperti rating, review, foto, jam buka, owner, telepon, website.

## Implementation Decision

Gunakan urutan ini:

1. Excel raw files tetap dianggap sumber mentah.
2. `jembrana_maps_base_clean.csv` dipakai sebagai staging dataset utama karena sudah dedup dan terfilter Jembrana.
3. Data dari Excel hanya dipakai ulang jika perlu audit asal-usul atau memperbaiki field yang hilang.
4. Jika lokasi dari soal rally muncul lagi, resolver mencari di:
   - historical waypoint DB,
   - `jembrana_maps_base_clean.csv`,
   - curated verified POI,
   - OSM/offline map,
   - Google validation saat online.
5. Lokasi baru dipromosikan ke curated database setelah navigator/field validation.

## Best Practice

Untuk sprint lapangan, tidak perlu import ulang semua Excel ke sistem. Lebih sederhana dan akurat:

- Pakai `jembrana_maps_base_clean.csv` sebagai source utama Jembrana.
- Simpan Excel sebagai raw audit evidence.
- Fokus pada validasi POI yang muncul di soal:
  - BR Bilukpoh Kangin,
  - BR Anyar Tembles,
  - SDN 1 Pergung,
  - SDN 2 Yeh Kuning,
  - BR Munduk Asem,
  - BR Puana,
  - BR Sri Mandala.

## Governance

Karena file ini membawa `place_id`, Google Maps URL, thumbnail, rating, review, dan metadata Google Places lain, statusnya tetap:

```text
source=google_validation_import
source_license=restricted_google_derived
verification_status=needs_field_verification
allowed_use=resolver_staging_google_validation_only
```

Keputusan akhir: **Excel ini boleh dipakai sebagai raw evidence dan staging support, tetapi untuk sistem repo gunakan CSV clean sebagai pintu masuk utama.**
