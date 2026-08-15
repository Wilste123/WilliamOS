-- WilliamOS auth + per-user data isolation
-- Run after 2026-08-13_unified_storage.sql
-- Idempotent where practical.

create extension if not exists "uuid-ossp";

create table if not exists user_profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null unique,
    full_name text not null,
    age integer,
    assistant_name text not null default 'WilliamOS',
    created_at timestamptz not null default now(),
    updated_at timestamptz
);

alter table user_profiles add column if not exists email text;
alter table user_profiles add column if not exists full_name text;
alter table user_profiles add column if not exists age integer;
alter table user_profiles add column if not exists assistant_name text not null default 'WilliamOS';
alter table user_profiles add column if not exists created_at timestamptz not null default now();
alter table user_profiles add column if not exists updated_at timestamptz;

alter table assets add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table projects add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table tasks add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table documents add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table decisions add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table events add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table inbox_items add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table memory_items add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table chat_history add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table requests_log add column if not exists user_id uuid references auth.users(id) on delete cascade;

create index if not exists idx_assets_user_id on assets(user_id);
create index if not exists idx_projects_user_id on projects(user_id);
create index if not exists idx_tasks_user_id on tasks(user_id);
create index if not exists idx_documents_user_id on documents(user_id);
create index if not exists idx_decisions_user_id on decisions(user_id);
create index if not exists idx_events_user_id on events(user_id);
create index if not exists idx_inbox_items_user_id on inbox_items(user_id);
create index if not exists idx_memory_items_user_id on memory_items(user_id);
create index if not exists idx_chat_history_user_id on chat_history(user_id);
create index if not exists idx_requests_log_user_id on requests_log(user_id);

alter table user_profiles enable row level security;
alter table assets enable row level security;
alter table projects enable row level security;
alter table tasks enable row level security;
alter table documents enable row level security;
alter table decisions enable row level security;
alter table events enable row level security;
alter table inbox_items enable row level security;
alter table memory_items enable row level security;
alter table chat_history enable row level security;
alter table requests_log enable row level security;

drop policy if exists "user_profiles_self_select" on user_profiles;
create policy "user_profiles_self_select"
    on user_profiles for select
    using (auth.uid() = id);

drop policy if exists "user_profiles_self_insert" on user_profiles;
create policy "user_profiles_self_insert"
    on user_profiles for insert
    with check (auth.uid() = id);

drop policy if exists "user_profiles_self_update" on user_profiles;
create policy "user_profiles_self_update"
    on user_profiles for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

drop policy if exists "assets_owner_only" on assets;
create policy "assets_owner_only"
    on assets for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "projects_owner_only" on projects;
create policy "projects_owner_only"
    on projects for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "tasks_owner_only" on tasks;
create policy "tasks_owner_only"
    on tasks for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "documents_owner_only" on documents;
create policy "documents_owner_only"
    on documents for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "decisions_owner_only" on decisions;
create policy "decisions_owner_only"
    on decisions for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "events_owner_only" on events;
create policy "events_owner_only"
    on events for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "inbox_items_owner_only" on inbox_items;
create policy "inbox_items_owner_only"
    on inbox_items for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "memory_items_owner_only" on memory_items;
create policy "memory_items_owner_only"
    on memory_items for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "chat_history_owner_only" on chat_history;
create policy "chat_history_owner_only"
    on chat_history for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists "requests_log_owner_only" on requests_log;
create policy "requests_log_owner_only"
    on requests_log for all
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);
