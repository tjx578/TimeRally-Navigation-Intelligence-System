# Master Clock dan Tap Detik

Referensi lokal yang dipakai:

- `D:\TIME RALLY\Dokumen_Teks\navipro-calculation-guide.yaml.txt`
- `D:\TIME RALLY\Dokumen_Teks\Estimasi Waktu Berdasarkan Jarak dan Kecepatan.txt`

Dokumen lokal menegaskan bahwa waktu start harus ditanyakan kepada user, lalu waktu start tiap sub-trayek ditambahkan berdasarkan durasi sub sebelumnya. Perhitungan waktu resmi pada jarak tertentu memakai:

`Waktu Berdasarkan Jarak = (Jarak Trip Odo x 60) / Kecepatan + Waktu Mulai Sub-Trayek`

## Implementasi UI

1. Navigator menginput jam start rally, contoh `08:00`.
2. Sistem membuat jadwal:
   - Sub A: `08:00 - 08:12`
   - Sub B: `08:12 - 08:50`
   - Sub C: `08:50 - 10:05`
   - dan seterusnya.
3. Tabel validasi timing menampilkan start, finish, mode kecepatan, jarak, waktu, speed, dan `km/detik`.
4. Jam master membaca jam perangkat dan memilih sub aktif otomatis.
5. Saat sisa waktu sub aktif <= 60 detik, UI menampilkan peringatan transisi.
6. Saat waktu habis, sub aktif pindah ke segmen berikutnya.

## Tap Detik

Untuk sub `Kecepatan tetap detik`, sistem menampilkan laju jarak:

`km/detik = km/jam / 3600`

Contoh sub C:

`19,90 / 3600 = 0,005528 km/detik`

Jika sub C mulai `08:50`, maka pada detik ke-120 jarak acuan:

`120 x 0,005528 = 0,663 km`

Angka jarak acuan inilah yang dibandingkan driver dengan odo mobil.

## Waktu Waypoint

Setelah navigator menekan `Finish Sub Ini` dan rute masuk roadbook, setiap waypoint dalam sub dapat diberi waktu resmi:

`waktu waypoint = start sub + (jarak kumulatif waypoint x 60 / speed sub)`

Ini membuat sistem tidak hanya mengunci jalur, tetapi juga mengunci target waktu di setiap waypoint.
