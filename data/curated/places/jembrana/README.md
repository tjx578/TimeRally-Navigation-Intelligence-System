# Jembrana Curated Places

Folder ini untuk POI Jembrana yang sudah boleh dipakai sebagai master offline resolver.

Sumber yang boleh masuk:
- manual survey,
- field GPS verification,
- KMPAL verified,
- OSM-compliant data dengan attribution,
- sumber lokal yang izin penyimpanannya jelas.

Sumber staging Google validation tidak boleh langsung dipromosikan tanpa proses verifikasi.

Recommended files:

```text
jembrana_verified_places.geojson
jembrana_place_aliases.csv
jembrana_verification_log.csv
```

Minimal verification fields:

```text
place_id,name,aliases,category,lat,lng,source,source_license,verification_status,verified_at,verification_method,notes
```
