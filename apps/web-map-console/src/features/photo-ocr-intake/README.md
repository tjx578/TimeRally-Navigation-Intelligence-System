# Photo OCR Intake

Fitur ini adalah pintu masuk soal berbentuk foto.

## Kontrol UI

- `Foto`: membuka kamera tablet/ponsel melalui input `capture=environment`.
- `Upload`: memilih satu atau beberapa gambar soal.
- Status OCR: memperlihatkan tahap foto diterima, OCR, parsing, validasi timing, mapping sub-trayek, dan roadbook ready.
- Field otomatis: lomba, trayek, lokasi, total jarak, dan total waktu.

## Pipeline

1. Browser menerima gambar.
2. Gambar dikirim ke worker OCR.
3. OCR menghasilkan teks dan confidence per halaman.
4. Parser membuat header dan sub-trayek.
5. Timing validator mengisi jarak, waktu, dan kecepatan.
6. Sub-trayek mapper membuat kandidat route per sub.
7. Navigator memilih sub di panel mapping dan mengunci hasil ke roadbook.
