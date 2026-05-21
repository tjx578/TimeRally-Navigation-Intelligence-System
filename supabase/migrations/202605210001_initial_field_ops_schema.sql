create extension if not exists pgcrypto;
create extension if not exists postgis;
create schema if not exists private;

create table if not exists public.rally_events (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  event_date date,
  region text,
  status text not null default 'draft'
    check (status in ('draft', 'field_test', 'locked', 'running', 'completed', 'archived')),
  source_type text not null default 'manual',
  owner_id uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rally_event_members (
  event_id uuid not null references public.rally_events(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'navigator', 'mapper', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (event_id, user_id)
);

create table if not exists public.rally_raw_inputs (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  kind text not null check (kind in ('photo', 'ocr_text', 'manual_text', 'fixture')),
  storage_path text,
  raw_text text,
  ocr_status text not null default 'pending'
    check (ocr_status in ('pending', 'processing', 'ready', 'failed', 'manual_required')),
  metadata jsonb not null default '{}'::jsonb,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.rally_trayeks (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  label text not null,
  total_distance_km numeric(8,3),
  total_time_minutes numeric(8,3),
  rally_start_time time,
  created_at timestamptz not null default now(),
  unique (event_id, label)
);

create table if not exists public.rally_sub_trayeks (
  id uuid primary key default gen_random_uuid(),
  trayek_id uuid not null references public.rally_trayeks(id) on delete cascade,
  label text not null,
  title text not null default '',
  sequence int not null,
  distance_km numeric(8,3),
  duration_minutes numeric(8,3),
  speed_mode text not null default 'unknown'
    check (speed_mode in ('liaison_zero_trip', 'average_speed', 'fixed_second', 'remaining_distance', 'unknown')),
  distance_counted_in_total boolean not null default true,
  status text not null default 'needs_review'
    check (status in ('needs_review', 'validated', 'locked', 'violation')),
  unique (trayek_id, label)
);

create table if not exists public.rally_waypoints (
  id uuid primary key default gen_random_uuid(),
  sub_trayek_id uuid not null references public.rally_sub_trayeks(id) on delete cascade,
  external_id text,
  sequence int not null,
  raw_text text not null,
  normalized_name text,
  action text,
  landmark_type text,
  relation text,
  kmpal_marker text,
  source text not null default 'manual',
  verification_status text not null default 'unresolved'
    check (verification_status in ('verified', 'inferred', 'needs_review', 'unresolved', 'rejected')),
  confidence numeric(5,4) not null default 0,
  coordinate geography(point, 4326),
  notes text[] not null default '{}',
  metadata jsonb not null default '{}'::jsonb,
  unique (sub_trayek_id, sequence)
);

create table if not exists public.rally_route_segments (
  id uuid primary key default gen_random_uuid(),
  sub_trayek_id uuid not null references public.rally_sub_trayeks(id) on delete cascade,
  from_waypoint_id uuid references public.rally_waypoints(id) on delete set null,
  to_waypoint_id uuid references public.rally_waypoints(id) on delete set null,
  sequence int not null,
  provider text not null default 'valhalla',
  distance_m int not null check (distance_m >= 0),
  duration_s int not null check (duration_s >= 0),
  status text not null default 'needs_review'
    check (status in ('ok', 'needs_review', 'warning', 'violation')),
  polyline_geojson jsonb not null default '{"type":"LineString","coordinates":[]}'::jsonb,
  route_realism_ratio numeric(7,3),
  created_at timestamptz not null default now(),
  unique (sub_trayek_id, sequence)
);

create table if not exists public.rally_candidate_reviews (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  waypoint_text text not null,
  candidate_name text not null,
  candidate_coordinate geography(point, 4326),
  source text not null default 'marshal',
  confidence numeric(5,4) not null default 0,
  decision text not null default 'pending'
    check (decision in ('pending', 'accepted', 'rejected')),
  reasons text[] not null default '{}',
  reviewed_by uuid references auth.users(id) on delete set null,
  reviewed_at timestamptz
);

create table if not exists public.rally_export_artifacts (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  format text not null,
  storage_path text not null,
  size_bytes bigint,
  checksum_sha256 text,
  generated_by uuid references auth.users(id) on delete set null,
  generated_at timestamptz not null default now()
);

create table if not exists public.rally_field_sessions (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  device_id text not null,
  status text not null default 'ready'
    check (status in ('ready', 'running', 'paused', 'completed', 'failed')),
  started_at timestamptz,
  finished_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.rally_field_positions (
  id bigint generated by default as identity primary key,
  session_id uuid not null references public.rally_field_sessions(id) on delete cascade,
  recorded_at timestamptz not null,
  coordinate geography(point, 4326) not null,
  speed_kmh numeric(7,3),
  bearing numeric(7,3),
  accuracy_m numeric(7,3)
);

create table if not exists public.rally_audit_logs (
  id bigint generated by default as identity primary key,
  event_id uuid references public.rally_events(id) on delete cascade,
  actor_id uuid references auth.users(id) on delete set null,
  action text not null,
  entity_table text not null,
  entity_id text,
  before_data jsonb,
  after_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists rally_waypoints_coordinate_gix on public.rally_waypoints using gist (coordinate);
create index if not exists rally_candidate_reviews_coordinate_gix on public.rally_candidate_reviews using gist (candidate_coordinate);
create index if not exists rally_field_positions_coordinate_gix on public.rally_field_positions using gist (coordinate);
create index if not exists rally_field_positions_session_time_idx on public.rally_field_positions (session_id, recorded_at desc);
create index if not exists rally_raw_inputs_event_idx on public.rally_raw_inputs (event_id, created_at desc);
create index if not exists rally_audit_logs_event_idx on public.rally_audit_logs (event_id, created_at desc);

alter table public.rally_events enable row level security;
alter table public.rally_event_members enable row level security;
alter table public.rally_raw_inputs enable row level security;
alter table public.rally_trayeks enable row level security;
alter table public.rally_sub_trayeks enable row level security;
alter table public.rally_waypoints enable row level security;
alter table public.rally_route_segments enable row level security;
alter table public.rally_candidate_reviews enable row level security;
alter table public.rally_export_artifacts enable row level security;
alter table public.rally_field_sessions enable row level security;
alter table public.rally_field_positions enable row level security;
alter table public.rally_audit_logs enable row level security;

create or replace function private.is_rally_event_member(target_event_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, private
as $$
  select exists (
    select 1
    from public.rally_event_members member
    where member.event_id = target_event_id
      and member.user_id = (select auth.uid())
  )
  or exists (
    select 1
    from public.rally_events event
    where event.id = target_event_id
      and event.owner_id = (select auth.uid())
  );
$$;

create or replace function private.is_rally_event_admin(target_event_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, private
as $$
  select exists (
    select 1
    from public.rally_event_members member
    where member.event_id = target_event_id
      and member.user_id = (select auth.uid())
      and member.role in ('owner', 'admin')
  )
  or exists (
    select 1
    from public.rally_events event
    where event.id = target_event_id
      and event.owner_id = (select auth.uid())
  );
$$;

grant usage on schema private to authenticated;
grant execute on function private.is_rally_event_member(uuid) to authenticated;
grant execute on function private.is_rally_event_admin(uuid) to authenticated;

create policy "event owners can create events"
on public.rally_events for insert to authenticated
with check (owner_id = (select auth.uid()));

create policy "members can view events"
on public.rally_events for select to authenticated
using (private.is_rally_event_member(id));

create policy "admins can update events"
on public.rally_events for update to authenticated
using (private.is_rally_event_admin(id))
with check (private.is_rally_event_admin(id));

create policy "members can view event membership"
on public.rally_event_members for select to authenticated
using (private.is_rally_event_member(event_id));

create policy "admins can manage event membership"
on public.rally_event_members for all to authenticated
using (private.is_rally_event_admin(event_id))
with check (private.is_rally_event_admin(event_id));

create policy "members can read raw inputs"
on public.rally_raw_inputs for select to authenticated
using (private.is_rally_event_member(event_id));

create policy "members can create raw inputs"
on public.rally_raw_inputs for insert to authenticated
with check (private.is_rally_event_member(event_id));

create policy "members can read trayeks"
on public.rally_trayeks for select to authenticated
using (private.is_rally_event_member(event_id));

create policy "members can write trayeks"
on public.rally_trayeks for all to authenticated
using (private.is_rally_event_member(event_id))
with check (private.is_rally_event_member(event_id));

create policy "members can read sub trayeks"
on public.rally_sub_trayeks for select to authenticated
using (
  exists (
    select 1 from public.rally_trayeks trayek
    where trayek.id = trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can write sub trayeks"
on public.rally_sub_trayeks for all to authenticated
using (
  exists (
    select 1 from public.rally_trayeks trayek
    where trayek.id = trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
)
with check (
  exists (
    select 1 from public.rally_trayeks trayek
    where trayek.id = trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can read waypoints"
on public.rally_waypoints for select to authenticated
using (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can write waypoints"
on public.rally_waypoints for all to authenticated
using (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
)
with check (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can read route segments"
on public.rally_route_segments for select to authenticated
using (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can write route segments"
on public.rally_route_segments for all to authenticated
using (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
)
with check (
  exists (
    select 1
    from public.rally_sub_trayeks sub
    join public.rally_trayeks trayek on trayek.id = sub.trayek_id
    where sub.id = sub_trayek_id
      and private.is_rally_event_member(trayek.event_id)
  )
);

create policy "members can manage candidate reviews"
on public.rally_candidate_reviews for all to authenticated
using (private.is_rally_event_member(event_id))
with check (private.is_rally_event_member(event_id));

create policy "members can read export artifacts"
on public.rally_export_artifacts for select to authenticated
using (private.is_rally_event_member(event_id));

create policy "members can create export artifacts"
on public.rally_export_artifacts for insert to authenticated
with check (private.is_rally_event_member(event_id));

create policy "members can manage field sessions"
on public.rally_field_sessions for all to authenticated
using (private.is_rally_event_member(event_id))
with check (private.is_rally_event_member(event_id));

create policy "members can read field positions"
on public.rally_field_positions for select to authenticated
using (
  exists (
    select 1 from public.rally_field_sessions session
    where session.id = session_id
      and private.is_rally_event_member(session.event_id)
  )
);

create policy "members can insert field positions"
on public.rally_field_positions for insert to authenticated
with check (
  exists (
    select 1 from public.rally_field_sessions session
    where session.id = session_id
      and private.is_rally_event_member(session.event_id)
  )
);

create policy "members can read audit logs"
on public.rally_audit_logs for select to authenticated
using (event_id is null or private.is_rally_event_member(event_id));

create policy "members can create audit logs"
on public.rally_audit_logs for insert to authenticated
with check (event_id is null or private.is_rally_event_member(event_id));
