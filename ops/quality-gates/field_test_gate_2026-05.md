# Field Test Quality Gate

Quality gate ini harus lulus sebelum test jalan nyata.

## Build Gate

- [ ] Backend Python compile berhasil.
- [ ] Frontend TypeScript build berhasil, atau alasan gagal dicatat.
- [ ] Tidak ada file konfigurasi secret masuk repo.

## Data Gate

- [ ] Soal real sudah menjadi fixture.
- [ ] OCR/manual text tersedia.
- [ ] Tabel timing sudah valid.
- [ ] Start manual bisa diubah.
- [ ] Finish total sesuai total waktu soal.

## UI Gate

- [ ] Foto/upload soal tersedia.
- [ ] Jam master tampil.
- [ ] Time.is/server/device status tampil.
- [ ] Tabel timing lengkap tampil.
- [ ] Sub A-G bisa diklik.
- [ ] Peta mengikuti sub aktif.
- [ ] Tombol finish sub bekerja.
- [ ] Roadbook bertambah.

## Timing Gate

- [ ] Sub start/finish benar.
- [ ] Countdown 60 detik benar.
- [ ] Auto-switch sub benar.
- [ ] km/detik benar.
- [ ] Jarak acuan tetap detik berjalan naik per detik.

## Offline Gate

- [ ] Halaman tetap bisa dibuka setelah refresh jika data sudah dimuat.
- [ ] Roadbook export tersedia sebagai backup.

## No-Go Conditions

Jangan turun field test jika salah satu terjadi:

- perhitungan jam sub salah,
- perhitungan km/detik salah,
- app crash di tablet,
- roadbook tidak bisa dibuat,
- data hilang setelah refresh,
- tidak ada backup manual.

