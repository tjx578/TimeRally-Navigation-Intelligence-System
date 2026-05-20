# Jembrana Historical Waypoints

Folder ini menyimpan waypoint yang muncul dari soal rally historis Jembrana.

Status data:
- `ocr_detected`: terbaca dari soal, belum punya koordinat.
- `matched_from_jembrana_csv`: cocok dengan staging CSV Jembrana, masih butuh validasi navigator.
- `partial_match_from_jembrana_csv`: cocok sebagian, perlu review lebih hati-hati.
- `needs_resolution`: belum ditemukan di database lokasi.

Data ini dipakai oleh place resolver sebagai memory historis. Jangan promosikan ke `data/curated/places/jembrana` sebelum diverifikasi navigator atau lapangan.
