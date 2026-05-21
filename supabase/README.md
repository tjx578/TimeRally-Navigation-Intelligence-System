# Supabase Production Schema

Folder ini berisi migration awal untuk backend persistence Time Rally.

Tujuan schema:

- menyimpan event, trayek, sub-trayek, waypoint, route segment, kandidat review,
  export artefak, dan audit field-session;
- memisahkan raw OCR/manual input dari data final yang dipakai lomba;
- mengaktifkan RLS pada semua tabel public;
- menghindari authorization berbasis `user_metadata`.

Catatan deployment:

1. Jalankan migration ke project Supabase staging dulu.
2. Pastikan Postgres/PostGIS tersedia.
3. Bila schema `public` diekspos melalui Data API, grant akses role
   `anon`/`authenticated` harus disesuaikan dengan setting project Supabase.
4. Gunakan bucket private untuk foto soal dan export pack; akses lewat signed URL.
5. Jalankan Supabase advisors sebelum production.

