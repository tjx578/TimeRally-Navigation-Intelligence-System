# Sub-Trayek Timing Validation

Fitur ini memvalidasi tabel waktu, jarak, dan kecepatan hasil OCR soal rally.

## Tujuan Navigator

- Memastikan setiap sub memiliki waktu dan jarak yang masuk akal.
- Memisahkan sub pengantar zero trip dari sub yang dihitung ke total jarak.
- Membandingkan total sub dengan total jarak dan total waktu pada header soal.
- Menandai konflik OCR sebelum rute dikunci atau dipakai untuk probabilitas jalur.

## Alur UI

1. OCR soal masuk ke input workbench.
2. Parser membentuk baris sub-trayek.
3. Navigator mengoreksi angka yang salah baca.
4. Panel validasi menghitung kecepatan tiap sub.
5. Sistem hanya memberi status `valid` kalau jarak dan waktu cocok dengan total soal.

## Aturan Bali Trayek 1

Sub A hanya menghitung waktu menuju zero trip. Sub B-G dihitung ke total jarak:

`20,10 + 8,90 + 14,40 + 8,40 + 5,30 + 8,00 = 65,10 km`

Waktu A-G:

`5 + 60 + 28 + 45 + 28 + 21 + 23 = 210 menit`
