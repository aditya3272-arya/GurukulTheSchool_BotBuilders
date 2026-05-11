-- Cortexia Supabase schema (run in Supabase SQL editor)

create extension if not exists "uuid-ossp";

-- Registered schools
create table if not exists public.schools (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  slug text unique,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Demo auth users (IDs + name) for Student/Staff, plus Visitor rows created on login
create table if not exists public.users (
  id uuid primary key default uuid_generate_v4(),
  school_id uuid not null references public.schools(id) on delete cascade,
  role text not null check (role in ('visitor','student','staff')),
  name text not null,
  adm_no text,
  staff_id text,
  created_at timestamptz not null default now()
);

create unique index if not exists users_school_admno_uq
  on public.users(school_id, adm_no)
  where adm_no is not null;

create unique index if not exists users_school_staffid_uq
  on public.users(school_id, staff_id)
  where staff_id is not null;

-- School knowledge items split by access level
create table if not exists public.knowledge_items (
  id uuid primary key default uuid_generate_v4(),
  school_id uuid not null references public.schools(id) on delete cascade,
  access_level text not null check (access_level in ('visitor','student','staff')),
  category text not null,
  title text not null,
  content text not null,
  source text,
  updated_at timestamptz not null default now()
);

create index if not exists knowledge_items_school_category_idx
  on public.knowledge_items(school_id, category);

create index if not exists knowledge_items_school_access_idx
  on public.knowledge_items(school_id, access_level);

-- Chat sessions/messages
create table if not exists public.chat_sessions (
  id uuid primary key default uuid_generate_v4(),
  school_id uuid not null references public.schools(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null default 'New chat',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists chat_sessions_user_updated_idx
  on public.chat_sessions(user_id, updated_at desc);

create table if not exists public.chat_messages (
  id uuid primary key default uuid_generate_v4(),
  session_id uuid not null references public.chat_sessions(id) on delete cascade,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists chat_messages_session_created_idx
  on public.chat_messages(session_id, created_at asc);

