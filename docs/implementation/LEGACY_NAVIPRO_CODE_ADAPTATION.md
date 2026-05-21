# Legacy NaviPRO Code Adaptation

Tanggal analisa: 2026-05-21

Sumber legacy dianalisa dari `D:\TIME RALLY\Kode_Python`.

## Ringkasan Per File

- `build_navipro_yaml.py`: membangun YAML NaviPRO dari hasil parse, dengan tabel waktu per sub-trayek dan format durasi.
- `championship_scoring_processor.py`: scoring 600 poin untuk distance, time formula, chaining, coordinate precision, continuity, knowledge bonus, dan klasifikasi juara.
- `file_converters.py`: converter CSV/Excel/JSON/GeoJSON/KML dan builder Google Maps link.
- `kmpal_processor_fixed.py`: resolver KMPAL dengan database region, compound marker, jarak Haversine, dan validasi toleransi.
- `kmpal_text_based.py kmpal_processor_fixed.py` dan `(1).py`: file kosong, tidak ada logic yang dapat diport.
- `lightweight_processor.py`: workflow ringan untuk parsing/resolusi dasar.
- `navipro_rally_processor.py` dan salinan `(1)`, `(2)`, `(3)`: duplikat identik, berisi orchestrator besar KMPAL, KML, regional boundary, Google Maps links, dan score.
- `offline_processor.py`: alur offline untuk pemrosesan tanpa internet.
- `rally_reasoning_processor.py`: decoder singkatan navigasi, BR/br case-sensitive, landmark parser, EAML/link generator.
- `SOP_STRICT_v8.py`: SOP zero-tolerance, waypoint wajib, URL Google Maps dengan semua waypoint.
- `sop_workflow_processor.py` dan `(1).py`: pipeline 4 step: parse struktur, validasi absolute constraint, chaining/maps integration, championship output.
- `sub_trayek_binding_enforcer.py`: enforcement jarak/waktu absolute per sub-trayek, severity, action required.
- `sub_trayek_parser_v3.py`: parser header `A.`, markdown `### **A...**`, mode Tetap Detik/Menit/Rata-rata/Bebas, titik navigasi.
- `technical_data_processor.py`: kalkulator speed/time, Haversine, route realism, YAML structure validator.
- `test_kmpal_complete.py`, `test_text_based.py`, `test_text_based (1).py`: test/demo untuk validasi KMPAL/text-based.
- `trayek3_absolute_parser.py`: parser khusus trayek 3/tulip dengan absolute binding.

## Logic Yang Diadaptasi Ke Repo

- Parser sekarang mendukung header legacy `A.`, `B.`, `### **A. ...**`, `Segmen A`, selain `Sub A`.
- Parser tidak lagi salah membaca `19,67 km/jam` sebagai jarak sub-trayek.
- Mode `Tetap Menit` dan `Santai/Bebas` ditambahkan sebagai `fixed_minute` dan `free_time`.
- Tokenizer mengenali KMPAL standalone seperti `KSM 2`, `DPS 11`, `CT 7`, bukan hanya compound `KSM 2/DPS 11/PNT 0`.
- Dictionary singkatan diperluas: `BKNT`, `BKRT`, `LRS`, `UJ`, `IJU`, `JB`, `SMPN`, `SMUN`, `KKD`, `PAD`, `PAM`, `PAR`, `TC`, `KA`, `DKT`, dan marker operasional lain.
- Constraint engine menambahkan detail severity championship berbasis toleransi legacy: <=2% aman, 2-5% review, >5% reject/disqualified.
- Scoring engine sekarang punya mode 600 poin dengan klasifikasi `JUARA NASIONAL`, `TINGKAT PROVINSI`, sampai `TIDAK MEMENUHI SYARAT`.
- KMPAL database sekarang dapat mengekstrak marker dari teks dan resolve compound/tunggal.

## Yang Tidak Diport Mentah-Mentah

- Database koordinat besar hardcoded di legacy tidak dipindahkan langsung karena sebagian tampak sebagai sampel/estimasi dan harus masuk `data/curated` setelah survey/verifikasi.
- Demo code, `print`, dan main script monolitik tidak dipindahkan karena repo production memakai modul, API, test, dan schema yang terpisah.
- Google Maps URL builder legacy tidak dijadikan sumber kebenaran routing; repo tetap routing-gateway/local-first lalu Google sebagai validator/link-out.

## Dampak Untuk Menyelesaikan Soal Rally

Adaptasi ini memperkuat tiga titik kritis lomba:

- soal OCR/manual dengan format event lama lebih mudah terbaca;
- KMPAL dan singkatan lokal lebih banyak dikenali sejak parser awal;
- hasil route bisa dinilai dengan score championship dan ditolak lebih cepat bila melanggar binding sub-trayek.
