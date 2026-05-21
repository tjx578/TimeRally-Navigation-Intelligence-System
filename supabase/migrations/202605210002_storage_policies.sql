-- Storage policies untuk Supabase Buckets sesuai deep-research-report.
--
-- Bucket yang harus dibuat dari dashboard atau CLI:
--   exports-private      (private)  -- artefak GPX/KML/YAML/Roadbook
--   uploads-private      (private)  -- foto soal rally / OCR input
--   assets-public        (public)   -- ikon, logo, style ringan
--   map-assets-public    (public)   -- PMTiles ringan / atribusi
--
-- Service role key MELEWATI RLS; itu tetap berlaku setelah migration ini.
-- Karena itu API harus mem-broker akses ke bucket private (signed URL).

-- ============= helpers =============
create or replace function private.bucket_path_event_id(path text)
returns uuid
language sql
immutable
as $$
  -- Konvensi penamaan: <event_id>/...filename
  -- Bila event_id tidak valid UUID, kembalikan null sehingga policy menolak.
  select case
    when path is null then null
    when split_part(path, '/', 1) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
      then split_part(path, '/', 1)::uuid
    else null
  end;
$$;

-- ============= uploads-private =============
-- Member event boleh upload foto/OCR di folder bertanda event_id.
create policy "uploads_private_member_insert"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'uploads-private'
  and private.is_rally_event_member(private.bucket_path_event_id(name))
);

create policy "uploads_private_member_select"
on storage.objects for select to authenticated
using (
  bucket_id = 'uploads-private'
  and private.is_rally_event_member(private.bucket_path_event_id(name))
);

create policy "uploads_private_admin_delete"
on storage.objects for delete to authenticated
using (
  bucket_id = 'uploads-private'
  and private.is_rally_event_admin(private.bucket_path_event_id(name))
);

-- ============= exports-private =============
-- Hanya admin event yang boleh menulis artefak final.
-- Member event boleh select sebagai metadata; pengunduhan dilakukan via signed URL
-- yang dibuat di server, sehingga anon TIDAK pernah mendapat akses langsung.
create policy "exports_private_admin_insert"
on storage.objects for insert to authenticated
with check (
  bucket_id = 'exports-private'
  and private.is_rally_event_admin(private.bucket_path_event_id(name))
);

create policy "exports_private_member_select"
on storage.objects for select to authenticated
using (
  bucket_id = 'exports-private'
  and private.is_rally_event_member(private.bucket_path_event_id(name))
);

create policy "exports_private_admin_delete"
on storage.objects for delete to authenticated
using (
  bucket_id = 'exports-private'
  and private.is_rally_event_admin(private.bucket_path_event_id(name))
);

-- ============= assets-public & map-assets-public =============
-- Bucket public sudah otomatis dapat akses read anon di Supabase.
-- Tetap kunci write hanya untuk admin agar konten public tidak bisa dipalsukan.
create policy "public_assets_admin_write"
on storage.objects for insert to authenticated
with check (
  bucket_id in ('assets-public', 'map-assets-public')
  and exists (
    select 1 from public.rally_events e
    where e.owner_id = (select auth.uid())
  )
);

create policy "public_assets_admin_update"
on storage.objects for update to authenticated
using (
  bucket_id in ('assets-public', 'map-assets-public')
  and exists (
    select 1 from public.rally_events e
    where e.owner_id = (select auth.uid())
  )
)
with check (
  bucket_id in ('assets-public', 'map-assets-public')
);

create policy "public_assets_admin_delete"
on storage.objects for delete to authenticated
using (
  bucket_id in ('assets-public', 'map-assets-public')
  and exists (
    select 1 from public.rally_events e
    where e.owner_id = (select auth.uid())
  )
);
