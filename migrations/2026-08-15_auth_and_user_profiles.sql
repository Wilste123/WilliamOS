-- WilliamOS Authentication & User Profiles Migration
-- Run in Supabase SQL editor or via psql.
-- Idempotent: safe to run multiple times.
-- Generated: 2026-08-15

-- ─────────────────────────────────────────────────────────────
-- user_profiles
-- Stores additional per-user info collected at registration.
-- The primary key (user_id) references auth.users managed by Supabase Auth.
-- ─────────────────────────────────────────────────────────────
create table if not exists user_profiles (
    user_id        uuid primary key references auth.users(id) on delete cascade,
    name           text,
    age            integer,
    assistant_name text not null default 'Jarvis',
    created_at     timestamptz not null default now(),
    updated_at     timestamptz
);

-- ─────────────────────────────────────────────────────────────
-- Row-Level Security (RLS) on user_profiles
-- Each user can only read/write their own row.
-- ─────────────────────────────────────────────────────────────
alter table user_profiles enable row level security;

drop policy if exists "users_own_profile" on user_profiles;
create policy "users_own_profile" on user_profiles
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────
-- Add user_id column to all data tables (nullable for backwards compat)
-- ─────────────────────────────────────────────────────────────
alter table assets        add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table projects      add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table tasks         add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table documents     add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table decisions     add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table events        add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table inbox_items   add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table memory_items  add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table chat_history  add column if not exists user_id uuid references auth.users(id) on delete set null;

-- ─────────────────────────────────────────────────────────────
-- Indexes on user_id for fast per-user queries
-- ─────────────────────────────────────────────────────────────
create index if not exists idx_assets_user_id       on assets(user_id);
create index if not exists idx_projects_user_id     on projects(user_id);
create index if not exists idx_tasks_user_id        on tasks(user_id);
create index if not exists idx_documents_user_id    on documents(user_id);
create index if not exists idx_decisions_user_id    on decisions(user_id);
create index if not exists idx_events_user_id       on events(user_id);
create index if not exists idx_inbox_items_user_id  on inbox_items(user_id);
create index if not exists idx_memory_items_user_id on memory_items(user_id);
create index if not exists idx_chat_history_user_id on chat_history(user_id);

-- ─────────────────────────────────────────────────────────────
-- Row-Level Security (RLS) on all data tables
-- Each user can only access rows that belong to them.
-- Rows with user_id IS NULL are excluded (legacy / admin rows).
-- ─────────────────────────────────────────────────────────────
alter table assets        enable row level security;
alter table projects      enable row level security;
alter table tasks         enable row level security;
alter table documents     enable row level security;
alter table decisions     enable row level security;
alter table events        enable row level security;
alter table inbox_items   enable row level security;
alter table memory_items  enable row level security;
alter table chat_history  enable row level security;

-- assets
drop policy if exists "users_own_assets"       on assets;
create policy "users_own_assets"       on assets
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- projects
drop policy if exists "users_own_projects"     on projects;
create policy "users_own_projects"     on projects
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- tasks
drop policy if exists "users_own_tasks"        on tasks;
create policy "users_own_tasks"        on tasks
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- documents
drop policy if exists "users_own_documents"    on documents;
create policy "users_own_documents"    on documents
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- decisions
drop policy if exists "users_own_decisions"    on decisions;
create policy "users_own_decisions"    on decisions
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- events
drop policy if exists "users_own_events"       on events;
create policy "users_own_events"       on events
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- inbox_items
drop policy if exists "users_own_inbox_items"  on inbox_items;
create policy "users_own_inbox_items"  on inbox_items
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- memory_items
drop policy if exists "users_own_memory_items" on memory_items;
create policy "users_own_memory_items" on memory_items
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);

-- chat_history
drop policy if exists "users_own_chat_history" on chat_history;
create policy "users_own_chat_history" on chat_history
    using  (auth.uid() = user_id)
    with check (auth.uid() = user_id);
