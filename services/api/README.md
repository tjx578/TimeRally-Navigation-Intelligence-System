# API Service

API adalah pintu masuk sistem.

## Tanggung Jawab

- Menerima input soal rally.
- Memanggil parser, resolver, routing gateway, constraint engine, probability engine, dan exporter.
- Mengembalikan output yang bisa dipakai UI dan field mobile.

## Endpoint Utama

```text
POST /v1/rally/parse
POST /v1/rally/resolve
POST /v1/rally/route
POST /v1/rally/validate
POST /v1/rally/infer-missing-waypoints
POST /v1/rally/export
```

## Prinsip

API tidak menyimpan logika rally berat. Logika rally berada di `packages/rally_core`.

