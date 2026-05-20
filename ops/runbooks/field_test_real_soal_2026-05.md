# Field Test Runbook - Real Soal

Runbook ini dipakai untuk test nyata minggu 11-17 Mei 2026.

## Tujuan

Membuktikan sistem bisa dipakai navigator dan driver di kendaraan dengan soal real.

Yang diuji:

1. Foto/upload soal.
2. OCR atau koreksi manual.
3. Tabel timing.
4. Jam master.
5. Tap detik.
6. Klik sub-trayek.
7. Roadbook.
8. Catatan deviasi lapangan.

## Persiapan H-1

Checklist teknis:

- [ ] Web UI bisa dibuka di tablet.
- [ ] Data soal test sudah masuk.
- [ ] Start time simulasi tersedia.
- [ ] Roadbook offline/export tersedia.
- [ ] Powerbank penuh.
- [ ] Internet mobile tersedia.
- [ ] Screenshot baseline jadwal A-G sudah disimpan.
- [ ] Backup manual berupa PDF/Markdown tersedia.

Checklist data:

- [ ] Nama event benar.
- [ ] Total jarak benar.
- [ ] Total waktu benar.
- [ ] Semua sub A-G terbaca.
- [ ] Mode kecepatan tiap sub benar.
- [ ] Sub tetap detik sudah punya km/detik.
- [ ] Sub tanpa jarak eksplisit diberi status review.

## Prosedur Field Test

1. Buka Web UI.
2. Pastikan status jam: Time.is/server/device terlihat.
3. Input start rally sesuai waktu test.
4. Foto/upload soal.
5. Pastikan tabel timing muncul.
6. Klik sub A dan cek peta.
7. Saat kendaraan mulai, tekan/konfirmasi start.
8. Jalankan sub A.
9. Pada 60 detik terakhir, cek countdown.
10. Saat sub berganti, pastikan sub aktif otomatis berubah.
11. Untuk sub tetap detik:
    - catat jarak acuan UI setiap 1 menit,
    - catat odo mobil di waktu yang sama,
    - catat selisih.
12. Tekan `Finish Sub Ini` setelah navigator mengunci sub.
13. Pastikan roadbook bertambah.
14. Ulangi minimal sampai 1 sub tetap detik selesai.

## Tabel Catatan Lapangan

| Waktu master | Sub | Jarak acuan UI | Odo mobil | Selisih | Catatan |
| --- | --- | ---: | ---: | ---: | --- |
| | | | | | |
| | | | | | |
| | | | | | |

## Acceptance Criteria

Sistem lulus field test jika:

- jadwal sub sesuai start manual,
- countdown muncul tepat 60 detik sebelum transisi,
- sub aktif berubah otomatis,
- tap detik berjalan sesuai rumus,
- roadbook bertambah setelah finish sub,
- navigator bisa bekerja tanpa bingung,
- driver bisa mengikuti jarak acuan.

## Evidence Yang Harus Dikumpulkan

- Screenshot jam master sebelum start.
- Screenshot tabel timing.
- Screenshot sub tetap detik sedang berjalan.
- Foto odo mobil pada minimal 3 titik.
- Catatan deviasi UI vs odo.
- Roadbook hasil finish sub.
- Daftar bug.

## Post-Test

1. Masukkan data deviasi ke fixture/golden test.
2. Tandai bug P0/P1/P2.
3. Tentukan apakah logic timing perlu diubah.
4. Freeze ulang roadbook jika hasil sudah benar.

