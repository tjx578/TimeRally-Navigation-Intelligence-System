# OCR Worker

Service produksi untuk intake foto soal. Worker bisa berjalan dalam dua mode:

- `OCR_ENGINE=google_vision`: memakai Google Cloud Vision `document_text_detection`.
- `OCR_ENGINE=disabled`: fallback aman, mengembalikan `manual_required`.

Walaupun OCR aktif, hasil tetap harus direview operator sebelum dipakai untuk
mapping/export lomba.

## Endpoints

- `GET /healthz`
- `GET /readyz`
- `POST /v1/ocr/photo`

## Environment

```text
OCR_ENGINE=google_vision
OCR_MIN_CONFIDENCE=0.1
```
