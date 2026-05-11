-- ============================================================
-- Cortexia — Full Schema
-- Run this first, before any seed files
-- ============================================================

create extension if not exists "uuid-ossp";

-- ──────────────────────────────────────────────────────────
-- SCHOOLS
-- ──────────────────────────────────────────────────────────
create table if not exists public.schools (
  id         uuid primary key default uuid_generate_v4(),
  name       text not null,
  slug       text unique,
  is_active  boolean not null default true,
  created_at timestamptz not null default now()
);

-- ──────────────────────────────────────────────────────────
-- USERS  (visitors, students, staff)
-- ──────────────────────────────────────────────────────────
create table if not exists public.users (
  id         uuid primary key default uuid_generate_v4(),
  school_id  uuid not null references public.schools(id) on delete cascade,
  role       text not null check (role in ('visitor','student','staff')),
  name       text not null,
  adm_no     text,
  staff_id   text,
  created_at timestamptz not null default now()
);

create unique index if not exists users_school_admno_uq
  on public.users(school_id, adm_no)
  where adm_no is not null;

create unique index if not exists users_school_staffid_uq
  on public.users(school_id, staff_id)
  where staff_id is not null;

-- ──────────────────────────────────────────────────────────
-- KNOWLEDGE ITEMS
-- ──────────────────────────────────────────────────────────
create table if not exists public.knowledge_items (
  id           uuid primary key default uuid_generate_v4(),
  school_id    uuid not null references public.schools(id) on delete cascade,
  access_level text not null check (access_level in ('visitor','student','staff')),
  category     text not null,
  title        text not null,
  content      text not null,
  source       text,
  updated_at   timestamptz not null default now()
);

create index if not exists knowledge_items_school_category_idx
  on public.knowledge_items(school_id, category);

create index if not exists knowledge_items_school_access_idx
  on public.knowledge_items(school_id, access_level);

-- ──────────────────────────────────────────────────────────
-- CHAT SESSIONS & MESSAGES
-- ──────────────────────────────────────────────────────────
create table if not exists public.chat_sessions (
  id         uuid primary key default uuid_generate_v4(),
  school_id  uuid not null references public.schools(id) on delete cascade,
  user_id    uuid not null references public.users(id) on delete cascade,
  title      text not null default 'New chat',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chat_sessions_user_updated_idx
  on public.chat_sessions(user_id, updated_at desc);

create table if not exists public.chat_messages (
  id         uuid primary key default uuid_generate_v4(),
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  role       text not null check (role in ('user','assistant','system')),
  content    text not null,
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_session_created_idx
  on public.chat_messages(session_id, created_at asc);

-- ──────────────────────────────────────────────────────────
-- STUDENT FEES
-- ──────────────────────────────────────────────────────────
create table if not exists public.student_fees (
  id             uuid primary key default gen_random_uuid(),
  school_id      uuid not null references public.schools(id) on delete cascade,
  adm_no         text not null,
  total_fees     numeric(10, 2) not null,
  paid_amount    numeric(10, 2) not null default 0,
  pending_amount numeric(10, 2) not null default 0,
  due_date       date not null,
  created_at     timestamptz default now()
);

alter table public.student_fees enable row level security;

drop policy if exists "Service Role Full Access" on public.student_fees;
create policy "Service Role Full Access" on public.student_fees
  for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');

-- ──────────────────────────────────────────────────────────
-- ADMIN CREDENTIALS
-- ──────────────────────────────────────────────────────────
create table if not exists public.admin_credentials (
  id            uuid primary key default uuid_generate_v4(),
  school_id     uuid not null references public.schools(id) on delete cascade,
  username      text not null,
  -- Store bcrypt hash, never plaintext. Generate at: bcrypt-generator.com (cost 12)
  password_hash text not null,
  display_name  text not null,
  is_active     boolean not null default true,
  last_login    timestamptz,
  created_at    timestamptz not null default now()
);

create unique index if not exists admin_credentials_school_username_uq
  on public.admin_credentials(school_id, username);

-- ──────────────────────────────────────────────────────────
-- CLASSES
-- ──────────────────────────────────────────────────────────
create table if not exists public.classes (
  id         uuid primary key default uuid_generate_v4(),
  school_id  uuid not null references public.schools(id) on delete cascade,
  name       text not null,    -- e.g. "9A"
  grade      int  not null,    -- e.g. 9
  section    text not null,    -- e.g. "A"
  created_at timestamptz not null default now(),
  unique (school_id, name)
);

-- ──────────────────────────────────────────────────────────
-- STUDENT ↔ CLASS LINKS
-- ──────────────────────────────────────────────────────────
create table if not exists public.student_classes (
  id         uuid primary key default uuid_generate_v4(),
  school_id  uuid not null references public.schools(id) on delete cascade,
  adm_no     text not null,
  class_id   uuid not null references public.classes(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (school_id, adm_no)
);

-- ──────────────────────────────────────────────────────────
-- TIMETABLE SLOTS
-- ──────────────────────────────────────────────────────────
create table if not exists public.timetable_slots (
  id               uuid primary key default uuid_generate_v4(),
  school_id        uuid not null references public.schools(id) on delete cascade,
  class_id         uuid not null references public.classes(id) on delete cascade,
  day              text not null check (day in ('Monday','Tuesday','Wednesday','Thursday','Friday')),
  period_number    int  not null check (period_number between 1 and 8),
  start_time       text not null,   -- e.g. "08:00"
  end_time         text not null,   -- e.g. "08:45"
  subject          text not null,
  teacher_staff_id text,            -- nullable for break / lunch periods
  is_break         boolean not null default false,
  created_at       timestamptz not null default now()
);

create index if not exists timetable_slots_class_day_idx
  on public.timetable_slots(class_id, day, period_number);

create index if not exists timetable_slots_teacher_idx
  on public.timetable_slots(school_id, teacher_staff_id);
