# OCR Soal dan Validasi Timing

Fitur ini menambahkan lapisan validasi angka sebelum sistem melakukan routing, probabilitas waypoint, atau ekspor roadbook.

## Masalah yang Diselesaikan

Soal rally sering berupa foto dengan kualitas berbeda. OCR bisa salah membaca angka `8,40` menjadi `84,0`, atau mencampur halaman dari trayek/event lain. Karena itu sistem tidak boleh langsung percaya pada teks OCR.

## Rancangan

1. Simpan gambar berdasarkan event dan lokasi seri.
2. Jalankan OCR per halaman dan simpan teks mentah beserta confidence.
3. Parser mencari header total jarak/waktu dan sub A, B, C, dan seterusnya.
4. Setiap sub dibuat menjadi baris `SubTrayekTimingRow`.
5. Validasi menghitung:
   - total jarak sub yang dihitung ke total,
   - total waktu semua sub,
   - kecepatan rata-rata tiap sub,
   - delta terhadap total pada header soal.
6. UI memberi status `valid`, `review`, atau `konflik`.

## Contoh Bali Trayek 1

Header soal menyatakan total jarak 65,10 km dan total waktu 210 menit.

Sub A adalah menuju zero trip selama 5 menit sehingga tidak dihitung ke total jarak.

Sub B-G menghasilkan total:

`20,10 + 8,90 + 14,40 + 8,40 + 5,30 + 8,00 = 65,10 km`

Sub A-G menghasilkan total waktu:

`5 + 60 + 28 + 45 + 28 + 21 + 23 = 210 menit`

Kesimpulan: pasangan halaman A-D dan E-G tersebut valid.

## Integrasi Web UI

Komponen `SubTrayekValidationPanel` ditempatkan di panel kanan agar navigator melihat validasi angka bersamaan dengan validasi championship dan opsi probabilitas rute. Saat jalur probabilitas muncul, navigator bisa memastikan dulu bahwa angka dasar sub-trayek sudah benar sebelum memilih opsi rute.

## Integrasi API

Endpoint `/v1/validation/timing-table` menerima daftar sub-trayek dan mengembalikan:

- total jarak hasil hitung,
- total waktu hasil hitung,
- delta terhadap target soal,
- kecepatan tiap sub,
- warning jika OCR belum lengkap atau total tidak cocok.
