# Production Sprint to Field Test

Tanggal sprint: Senin 11 Mei 2026 sampai Minggu 17 Mei 2026.

Target: sistem bisa dites nyata di lapangan memakai soal rally real, dengan fokus pada OCR/foto soal, validasi timing, jam master, tap detik, mapping sub-trayek, roadbook, dan logging hasil test.

## Prinsip Sprint

Keep it simple, accurate, testable.

Yang harus jadi minggu ini:

1. Web UI bisa menerima foto soal atau upload gambar.
2. OCR/manual correction bisa menghasilkan tabel sub-trayek.
3. Tabel timing menampilkan start, finish, jarak, waktu, speed, mode, dan km/detik.
4. Jam master memakai start manual navigator dan referensi Time.is/server time.
5. Sub aktif pindah otomatis sesuai jadwal.
6. Countdown 60 detik muncul sebelum pindah segmen.
7. Sub tetap detik menampilkan jarak acuan berjalan.
8. Navigator bisa klik sub A-G dan melihat rute sub aktif di peta.
9. Tombol `Finish Sub Ini` memasukkan sub ke roadbook.
10. Hasil test lapangan bisa dievaluasi sebagai golden test.

Yang tidak dikejar minggu ini:

1. Multi-provider routing lengkap.
2. Traccar/live tracking penuh.
3. RBAC production kompleks.
4. Observability stack besar.
5. Mobile APK native.

## Deliverable Produksi Minimum

| Area | Deliverable | Status minimum |
| --- | --- | --- |
| Repo | GitHub repo + branch `main`/`develop` | wajib |
| CI | Python compile + frontend build/lint jika dependencies tersedia | wajib |
| Data | 1 golden case dari soal Bali uploaded | wajib |
| UI | Foto/upload, timing table, master clock, sub map, roadbook | wajib |
| API | `/v1/rally/photo-ocr`, `/v1/validation/timing-table` | wajib |
| Offline | data hasil parse bisa tetap dibaca tanpa internet setelah load | minimal |
| Field test | minimal 1 trayek diuji nyata | wajib |

## Timeline Harian

### Senin 11 Mei 2026 - Freeze Scope dan Repo

Tujuan: repo siap dikembangkan serius.

Tasks:

1. Push skeleton ke GitHub.
2. Buat branch `develop`.
3. Tambahkan issue list untuk sprint.
4. Tambahkan `.env.example` yang realistis untuk dev.
5. Pastikan semua dokumen sprint/runbook masuk repo.
6. Pastikan contoh soal Bali uploaded menjadi fixture resmi.

Gate selesai:

- Repo bisa di-clone.
- Struktur app/API/docs/data terbaca jelas.
- Golden fixture `pertamina_merah_putih_bali_trayek_1_photo_ocr.json` ada.

### Selasa 12 Mei 2026 - Timing Engine dan Golden Test

Tujuan: angka tidak boleh salah.

Tasks:

1. Kunci schema `TimingRow`, `SubTrayek`, `RoadbookLeg`.
2. Buat test untuk:
   - start manual `08:00`,
   - finish total `12:30`,
   - sub C mulai `08:50`,
   - sub C km/detik `0.005528`,
   - countdown aktif di `08:49:00`.
3. Buat validator toleransi total jarak/waktu.
4. Buat command test golden case.

Gate selesai:

- Simulasi soal Bali menghasilkan jadwal A-G benar.
- Formula tap detik benar.
- Test bisa dijalankan lokal.

### Rabu 13 Mei 2026 - Web UI Operasional

Tujuan: navigator bisa memakai UI tanpa membaca kode.

Tasks:

1. Install dependencies web di environment dev.
2. Jalankan Vite dev server.
3. Uji UI:
   - input start rally,
   - tabel timing,
   - klik sub A-G,
   - peta berubah,
   - finish sub,
   - roadbook bertambah.
4. Tambahkan edit manual angka OCR di tabel jika belum ada.
5. Tambahkan status sumber jam: `Time.is`, `server`, atau `device`.

Gate selesai:

- UI bisa dipakai dari browser/tablet.
- Navigator bisa koreksi data tanpa edit file.

### Kamis 14 Mei 2026 - Routing dan Roadbook

Tujuan: sub-trayek menjadi rute yang bisa diikuti.

Tasks:

1. Untuk field test, boleh pakai rute manual/seeded jika routing engine belum siap.
2. Pastikan setiap sub punya:
   - start label,
   - finish label,
   - polyline atau waypoint list,
   - jarak,
   - start/finish time.
3. Export roadbook sederhana:
   - HTML/print,
   - JSON,
   - GPX/KML jika memungkinkan.
4. Buat tombol freeze package untuk test.

Gate selesai:

- Roadbook bisa dibuka sebelum field test.
- Setiap sub bisa diakses satu per satu.

### Jumat 15 Mei 2026 - Dry Run Indoor

Tujuan: cari error sebelum turun jalan.

Tasks:

1. Simulasi waktu dengan start palsu dekat waktu sekarang.
2. Cek auto-switch sub.
3. Cek countdown 60 detik.
4. Cek mode tetap detik.
5. Cek roadbook saat sub di-finish.
6. Catat bug P0/P1.

Gate selesai:

- Tidak ada bug P0.
- Bug P1 punya workaround.
- Field test route package sudah freeze.

### Sabtu 16 Mei 2026 - Field Test Nyata

Tujuan: uji sistem dengan kendaraan dan soal real.

Setup:

1. 1 tablet/HP navigator.
2. 1 HP backup.
3. Powerbank.
4. Soal foto asli.
5. Roadbook export offline.
6. Spreadsheet/notes untuk catatan aktual.

Test minimal:

1. Input start rally.
2. Jalankan sub A sampai finish.
3. Cek transisi A ke B.
4. Jalankan minimal 1 sub tetap detik, idealnya sub C.
5. Bandingkan jarak acuan tap detik vs odo mobil setiap 1 menit.
6. Catat deviasi waktu/jarak.
7. Simpan screenshot dan catatan.

Gate selesai:

- Sistem bisa dipakai di mobil.
- Navigator bisa mengikuti sub aktif.
- Driver memahami tap detik.
- Ada data deviasi lapangan.

### Minggu 17 Mei 2026 - Review dan Fix

Tujuan: hasil field test masuk golden test.

Tasks:

1. Rekap bug.
2. Rekap deviasi.
3. Update fixture expected output.
4. Tambahkan catatan field test ke docs.
5. Tentukan apakah lanjut ke routing engine/live GPS.

Gate selesai:

- Field test report selesai.
- Golden test diperbarui.
- Sprint berikutnya jelas.

## Go/No-Go Field Test

Go jika:

- soal bisa masuk UI,
- tabel timing benar,
- jam start bisa diubah manual,
- start/finish sub benar,
- countdown 60 detik berjalan,
- tap detik tampil untuk sub tetap detik,
- roadbook bisa dibuat,
- data bisa dibuka ulang tanpa hilang.

No-Go jika:

- waktu sub salah,
- tap detik salah,
- sub aktif tidak pindah sesuai waktu,
- roadbook tidak bisa dibuat,
- UI crash di tablet,
- data hilang setelah refresh.

## Bug Priority

P0:

- salah hitung waktu,
- salah hitung km/detik,
- sub aktif pindah salah,
- data roadbook hilang,
- app tidak bisa dibuka di field.

P1:

- peta tidak center,
- Time.is gagal tetapi fallback jam perangkat berjalan,
- upload foto gagal tetapi input manual masih bisa.

P2:

- tampilan kurang rapi,
- label kurang jelas,
- export tambahan belum lengkap.

