# ADR-0001: Hybrid Google and OSM Architecture

## Status

Accepted.

## Context

Time rally membutuhkan navigasi presisi, tetapi tidak selalu punya koneksi internet. Google Maps kuat untuk validasi online, Places, dan familiar link-out. Namun offline map tidak boleh dibangun dari cached Google tiles/content.

## Decision

Sistem menggunakan:
- OSM/Valhalla/OSRM/Nominatim untuk offline-first routing dan map.
- Google Maps sebagai online adapter dan validation provider.
- Source separation untuk setiap koordinat dan route result.

## Consequences

Positif:
- Sistem tetap berjalan offline.
- Tidak terkunci satu vendor.
- Data provenance jelas.
- Cocok untuk field rally.

Tradeoff:
- Butuh pipeline mapdata sendiri.
- Butuh governance data lebih ketat.
- Hasil OSM dan Google kadang berbeda, sehingga perlu provider comparison.

