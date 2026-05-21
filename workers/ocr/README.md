# OCR Worker

Service stub produksi untuk intake foto soal. Worker ini sengaja tidak
mengarang hasil OCR: sampai engine OCR final dipasang, endpoint mengembalikan
status `manual_required` agar operator tetap memasukkan teks hasil verifikasi.

## Endpoints

- `GET /healthz`
- `GET /readyz`
- `POST /v1/ocr/photo`
