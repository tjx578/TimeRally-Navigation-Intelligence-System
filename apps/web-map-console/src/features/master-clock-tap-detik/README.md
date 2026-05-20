# Master Clock dan Tap Detik

Fitur ini membuat waktu resmi rally menjadi acuan utama UI.

## Input Navigator

Navigator mengisi `Start rally`, misalnya `08:15`. Sistem lalu menghitung:

- start sub A,
- finish sub A/start sub B,
- finish sub B/start sub C,
- dan seterusnya sampai finish trayek.

## Perpindahan Otomatis

Jam master membaca jam perangkat. Ketika sisa waktu sub aktif tinggal 60 detik, UI menampilkan countdown pindah segmen. Setelah waktu sub habis, sub aktif otomatis mengikuti jadwal resmi berikutnya.

## Tap Detik

Untuk sub `Kecepatan tetap detik`, UI menampilkan:

`km/detik = kecepatan km/jam / 3600`

Jarak acuan berjalan:

`jarak acuan = detik berjalan sub x km/detik`

Driver membandingkan jarak ini dengan odo mobil. Jika odo mobil dan jarak acuan seirama, kendaraan sedang mengikuti irama waktu master.

## Waktu Waypoint

Setelah rute sub-trayek terkunci menjadi roadbook, setiap waypoint bisa diberi waktu resmi:

`waktu waypoint = start sub + (jarak kumulatif waypoint x 60 / kecepatan sub)`

Untuk sub tetap detik, rumus yang sama tetap dipakai, tetapi UI menekankan laju jarak per detik.
