# Route Editor and Probability UI

Dokumen ini menerjemahkan pola kerja Footpath ke kebutuhan Time Rally tanpa mengubah struktur asli sistem.

## Tujuan

Navigator dan analyst harus bisa memperbaiki rute yang dihasilkan sistem dengan cepat, terutama saat waypoint tidak ditemukan dan sistem memberi beberapa opsi jalur probabilitas.

## Prinsip UI

1. Soal rally tetap sumber utama.
2. Urutan waypoint tidak berubah otomatis.
3. Edit hanya mempengaruhi segmen aktif.
4. Setiap edit memicu revalidation pada sub-trayek terkait.
5. Jalur probabilitas tidak dianggap final sebelum dipilih atau dikunci.

## Layout Operasional

```text
┌────────────────────────────────────────────────────────────┐
│ Topbar: Event | Provider | Validation | Export             │
├───────────────┬─────────────────────────────┬──────────────┤
│ Input + Tools │ Map + Route Editor Toolbar  │ Validation   │
│ Route Editor  │ Draw / Erase / Repair       │ Probability  │
│               │ Candidate overlays          │ Waypoints    │
├───────────────┴─────────────────────────────┴──────────────┤
│ Roadbook: Leg | Instruksi | Jarak | ETA | Status           │
└────────────────────────────────────────────────────────────┘
```

## Route Editor Tools

### Inspect

Default mode untuk membaca rute, memilih waypoint, dan membuka detail confidence.

### Draw

Menggambar segmen baru. Jika `snap_to_road=true`, geometry dikirim ke routing provider untuk snap ke jalan. Jika off, geometry disimpan sebagai manual trace.

### Erase

Menghapus bagian segmen yang salah. Sistem otomatis menandai affected leg dan menjalankan ulang validasi.

### Repair

Mode untuk mengganti segmen lama dengan kandidat baru. Cocok saat rute probabilitas lebih masuk akal daripada hasil awal.

### Split

Membelah leg menjadi dua dengan waypoint baru. Cocok saat waypoint hilang ditemukan di tengah segmen.

### Lock

Mengunci route final agar tidak berubah saat provider comparison atau revalidation berjalan.

## Probability Route Options

Panel probabilitas menampilkan:

- nama kandidat,
- missing waypoint,
- confidence,
- provider,
- deviasi jarak,
- deviasi waktu,
- route corridor fit,
- alasan pemilihan,
- tombol pakai, tolak, bandingkan.

## Candidate Decision Flow

```text
candidate confidence >= 85%
  -> tampil sebagai recommended
  -> user boleh "Pakai"
  -> status menjadi accepted
  -> route segment diganti
  -> validate sub-trayek

70% <= confidence < 85%
  -> tampil sebagai review
  -> user wajib membandingkan atau cek manual

confidence < 70%
  -> tidak boleh auto apply
  -> status unresolved
```

## Behavior Saat Jalur Dipilih

1. Candidate route di-highlight di peta.
2. Leg lama tetap terlihat sebagai ghost/dashed line.
3. Panel memperlihatkan delta:
   - jarak lama vs baru,
   - waktu lama vs baru,
   - score lama vs baru.
4. Jika user memilih "Pakai", sistem membuat route edit operation.
5. Constraint engine menjalankan ulang validasi.

## Output Yang Harus Diupdate

Setelah edit:

- roadbook table,
- validation panel,
- route layers,
- candidate review log,
- export readiness.

## Data Audit

Setiap route edit harus menyimpan:

```yaml
operation: repair
snap_to_road: true
affected_leg_ids: [LEG-003]
reason: "Candidate confidence 88%, distance deviation 1.2%"
operator: analyst
timestamp: auto
```

## Best Practice Untuk Navigator

- Jangan gunakan auto-reroute untuk mengganti urutan soal.
- Pakai candidate tertinggi hanya jika constraint tetap compliant.
- Jika kandidat bagus tapi distance violation, gunakan mode repair/draw untuk menambahkan detour legal.
- Lock route hanya setelah semua inferred waypoint direview.

