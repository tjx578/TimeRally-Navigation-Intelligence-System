# Data Governance

## Data Sources

| Source | Boleh Disimpan? | Catatan |
|---|---|---|
| Manual survey | Ya | Sumber terbaik untuk rally. |
| KMPAL verified | Ya | Harus punya tanggal verifikasi. |
| Local curated POI | Ya | Berasal dari data yang boleh digunakan. |
| OSM | Ya | Ikuti ODbL attribution dan derivative database rules. |
| Google place_id | Ya | place_id boleh disimpan untuk lookup ulang. |
| Google lat/lng/content | Terbatas | Jangan dipakai untuk offline map permanen. |
| Google tiles | Tidak untuk offline | Jangan cache untuk offline navigation. |

## Google Validation Staging

Dataset yang berasal dari Google Maps/Places atau hasil scraping/ekspor yang membawa `place_id`, Google Maps URL, foto, review, rating, jam buka, atau konten bisnis harus masuk ke:

```text
data/raw/google_validation/<region>/
```

Aturan:
- `place_id` boleh disimpan untuk lookup ulang.
- data staging boleh membantu OCR waypoint resolver dan validasi online.
- data staging tidak boleh langsung menjadi master POI offline.
- rating, review, foto, jam operasional, owner, website, dan telepon tidak disalin ke curated offline database kecuali ada dasar izin/sumber lain yang jelas.
- promosi ke `data/curated/places` wajib melalui manual survey, KMPAL verified, OSM-compliant source, atau sumber lokal yang jelas izinnya.
- UI harus membedakan kandidat `google_validation` dari kandidat `verified`.

## Place Record

```yaml
place:
  id: "poi_000001"
  name: "Balai Banjar Example"
  aliases: ["br example", "banjar example"]
  category: "balai_masyarakat"
  lat: -8.650000
  lng: 115.216667
  source: "manual_survey"
  source_license: "internal_verified"
  confidence: 0.98
  verified_at: "2026-05-07"
  verification_method: "field_gps"
  google_place_id: null
  osm_id: null
```

## Required Indexes

Untuk performa:
- name trigram index,
- alias index,
- category index,
- geospatial index,
- source/confidence index,
- KMPAL code index.

## Data Quality Flags

```text
verified
needs_review
duplicate_candidate
source_conflict
low_precision_coordinate
outside_region
stale_verification
```
