-- Cloud SQL PostgreSQL + PostGIS adaptation of the Supabase field ops schema.
-- This migration avoids Supabase-only auth/storage objects so the same rally
-- domain tables can run on Google Cloud SQL. For fast field tests, enforce
-- user/event authorization in the API first; PostgreSQL RLS can be layered in a
-- later migration once the Cloud auth model is final.

create extension if not exists pgcrypto;
create extension if not exists postgis;
create extension if not exists postgis_topology;

create table if not exists public.rally_app_users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text,
  provider text not null default 'cloudsql',
  provider_subject text,
  role text not null default 'operator'
    check (role in ('owner', 'admin', 'navigator', 'mapper', 'viewer', 'operator')),
  created_at timestamptz not null default now()
);

create table if not exists public.rally_events (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  event_date date,
  region text,
  status text not null default 'draft'
    check (status in ('draft', 'field_test', 'locked', 'running', 'completed', 'archived')),
  source_type text not null default 'manual',
  owner_id uuid references public.rally_app_users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rally_event_members (
  event_id uuid not null references public.rally_events(id) on delete cascade,
  user_id uuid not null references public.rally_app_users(id) on delete cascade,
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
  created_by uuid references public.rally_app_users(id) on delete set null,
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
  provider text not null default 'auto',
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
  reviewed_by uuid references public.rally_app_users(id) on delete set null,
  reviewed_at timestamptz
);

create table if not exists public.rally_export_artifacts (
  id uuid primary key default gen_random_uuid(),
  event_id uuid not null references public.rally_events(id) on delete cascade,
  format text not null,
  storage_path text not null,
  size_bytes bigint,
  checksum_sha256 text,
  generated_by uuid references public.rally_app_users(id) on delete set null,
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
  actor_id uuid references public.rally_app_users(id) on delete set null,
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
