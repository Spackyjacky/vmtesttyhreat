-- ============================================================
--  Repair Shop — Supabase Schema
--  Run this in the Supabase SQL Editor (supabase.com → your project → SQL Editor)
-- ============================================================

-- Enable UUID generation
create extension if not exists "uuid-ossp";

-- ────────────────────────────────────────────
--  CUSTOMERS
-- ────────────────────────────────────────────
create table if not exists customers (
  id          uuid primary key default uuid_generate_v4(),
  name        text not null,
  phone       text,
  email       text,
  notes       text,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

create index if not exists idx_customers_name  on customers (name);
create index if not exists idx_customers_phone on customers (phone);
create index if not exists idx_customers_email on customers (email);

-- ────────────────────────────────────────────
--  JOBS
-- ────────────────────────────────────────────
create table if not exists jobs (
  id               uuid primary key default uuid_generate_v4(),
  ticket_number    serial not null,
  customer_id      uuid references customers (id) on delete set null,

  -- Device info
  device_type      text not null check (device_type in ('phone','tablet','computer','console','other')),
  device_make      text not null,
  device_model     text not null,
  imei             text,
  reported_fault   text not null,

  -- Security / data
  password         text,
  backup_required  boolean default false,
  backup_completed boolean default false,

  -- Workflow
  status           text not null default 'intake'
                   check (status in ('intake','diagnosed','in_progress','waiting_parts','ready','collected')),
  technician_name  text,

  -- Financials
  quoted_price     numeric(10,2),
  final_price      numeric(10,2),

  -- Notes
  notes            text,
  internal_notes   text,

  created_at       timestamptz default now(),
  updated_at       timestamptz default now(),
  collected_at     timestamptz
);

create index if not exists idx_jobs_status      on jobs (status);
create index if not exists idx_jobs_customer_id on jobs (customer_id);
create index if not exists idx_jobs_created_at  on jobs (created_at desc);

-- ────────────────────────────────────────────
--  JOB PHOTOS
-- ────────────────────────────────────────────
create table if not exists job_photos (
  id          uuid primary key default uuid_generate_v4(),
  job_id      uuid not null references jobs (id) on delete cascade,
  url         text not null,
  photo_type  text not null check (photo_type in ('intake','damage','repair','completion')),
  caption     text,
  created_at  timestamptz default now()
);

create index if not exists idx_job_photos_job_id on job_photos (job_id);

-- ────────────────────────────────────────────
--  SIGNATURES
-- ────────────────────────────────────────────
create table if not exists signatures (
  id             uuid primary key default uuid_generate_v4(),
  job_id         uuid not null references jobs (id) on delete cascade unique,
  signature_url  text not null,
  collected_by   text,
  customer_name  text,
  created_at     timestamptz default now()
);

-- ────────────────────────────────────────────
--  INVENTORY
-- ────────────────────────────────────────────
create table if not exists inventory (
  id                 uuid primary key default uuid_generate_v4(),
  part_name          text not null,
  sku                text,
  description        text,
  quantity           integer not null default 0,
  reorder_threshold  integer default 5,
  cost_price         numeric(10,2),
  sell_price         numeric(10,2),
  supplier           text,
  created_at         timestamptz default now(),
  updated_at         timestamptz default now()
);

create index if not exists idx_inventory_sku on inventory (sku);

-- ────────────────────────────────────────────
--  JOB PARTS (parts used on a job)
-- ────────────────────────────────────────────
create table if not exists job_parts (
  id            uuid primary key default uuid_generate_v4(),
  job_id        uuid not null references jobs (id) on delete cascade,
  inventory_id  uuid references inventory (id) on delete set null,
  part_name     text not null,
  quantity      integer not null default 1,
  unit_price    numeric(10,2),
  created_at    timestamptz default now()
);

create index if not exists idx_job_parts_job_id on job_parts (job_id);

-- ────────────────────────────────────────────
--  NOTIFICATION LOG
-- ────────────────────────────────────────────
create table if not exists notification_log (
  id         uuid primary key default uuid_generate_v4(),
  job_id     uuid not null references jobs (id) on delete cascade,
  type       text not null check (type in ('sms','email')),
  recipient  text not null,
  message    text,
  status     text default 'sent',
  sent_at    timestamptz default now()
);

create index if not exists idx_notification_log_job_id on notification_log (job_id);

-- ────────────────────────────────────────────
--  AUTO-UPDATE updated_at
-- ────────────────────────────────────────────
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace trigger customers_updated_at
  before update on customers
  for each row execute function update_updated_at();

create or replace trigger jobs_updated_at
  before update on jobs
  for each row execute function update_updated_at();

create or replace trigger inventory_updated_at
  before update on inventory
  for each row execute function update_updated_at();

-- ────────────────────────────────────────────
--  ROW LEVEL SECURITY
--  Authenticated users (your staff) can read/write everything.
--  The collect page uses the service-role key server-side only.
-- ────────────────────────────────────────────
alter table customers        enable row level security;
alter table jobs             enable row level security;
alter table job_photos       enable row level security;
alter table signatures       enable row level security;
alter table inventory        enable row level security;
alter table job_parts        enable row level security;
alter table notification_log enable row level security;

-- Authenticated users: full access
create policy "auth full access" on customers        for all to authenticated using (true) with check (true);
create policy "auth full access" on jobs             for all to authenticated using (true) with check (true);
create policy "auth full access" on job_photos       for all to authenticated using (true) with check (true);
create policy "auth full access" on signatures       for all to authenticated using (true) with check (true);
create policy "auth full access" on inventory        for all to authenticated using (true) with check (true);
create policy "auth full access" on job_parts        for all to authenticated using (true) with check (true);
create policy "auth full access" on notification_log for all to authenticated using (true) with check (true);

-- ────────────────────────────────────────────
--  STORAGE BUCKET for photos & signatures
-- ────────────────────────────────────────────
-- Run this separately in the Storage section or via the SQL editor:
-- insert into storage.buckets (id, name, public) values ('repair-media', 'repair-media', true);
