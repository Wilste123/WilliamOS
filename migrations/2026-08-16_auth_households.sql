-- WilliamOS Auth + Households Migration
-- Run in Supabase SQL editor.
-- Idempotent where possible.
-- Generated: 2026-08-16
--
-- BEFORE YOU RUN:
-- 1. Enable Email auth in Supabase Dashboard -> Authentication -> Providers
-- 2. For dev/testing, disable "Confirm email" under Authentication -> Settings
-- 3. Use SUPABASE_ANON_KEY (not service role) in the app's .env

create extension if not exists "uuid-ossp";

-- ─────────────────────────────────────────────────────────────
-- Households
-- ─────────────────────────────────────────────────────────────
create table if not exists households (
    id          uuid primary key default uuid_generate_v4(),
    name        text not null,
    created_by  uuid references auth.users(id) on delete set null,
    created_at  timestamptz not null default now()
);

create table if not exists household_members (
    id            uuid primary key default uuid_generate_v4(),
    household_id  uuid not null references households(id) on delete cascade,
    user_id       uuid not null references auth.users(id) on delete cascade,
    role          text not null default 'member' check (role in ('owner', 'member')),
    joined_at     timestamptz not null default now(),
    unique (household_id, user_id)
);

create table if not exists user_profiles (
    id                    uuid primary key references auth.users(id) on delete cascade,
    display_name          text,
    default_household_id  uuid references households(id) on delete set null,
    created_at            timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- Auth columns on existing tables
-- ─────────────────────────────────────────────────────────────
do $$
declare
    tbl text;
begin
    foreach tbl in array array[
        'assets', 'projects', 'tasks', 'documents', 'decisions',
        'events', 'inbox_items', 'memory_items', 'requests_log', 'chat_history'
    ]
    loop
        execute format('alter table %I add column if not exists user_id uuid references auth.users(id) on delete set null', tbl);
        execute format('alter table %I add column if not exists household_id uuid references households(id) on delete set null', tbl);
        execute format('alter table %I add column if not exists visibility text not null default ''household''', tbl);
        execute format('alter table %I drop constraint if exists %I_visibility_check', tbl, tbl);
        execute format(
            'alter table %I add constraint %I_visibility_check check (visibility in (''private'', ''household''))',
            tbl, tbl
        );
    end loop;
end $$;

-- Private-by-default tables
alter table inbox_items alter column visibility set default 'private';
alter table memory_items alter column visibility set default 'private';
alter table requests_log alter column visibility set default 'private';
alter table chat_history alter column visibility set default 'private';

-- ─────────────────────────────────────────────────────────────
-- Indexes
-- ─────────────────────────────────────────────────────────────
create index if not exists idx_household_members_user_id on household_members(user_id);
create index if not exists idx_household_members_household_id on household_members(household_id);
create index if not exists idx_assets_household_id on assets(household_id);
create index if not exists idx_assets_user_id on assets(user_id);
create index if not exists idx_tasks_household_id on tasks(household_id);
create index if not exists idx_tasks_user_id on tasks(user_id);
create index if not exists idx_documents_household_id on documents(household_id);
create index if not exists idx_documents_user_id on documents(user_id);
create index if not exists idx_events_household_id on events(household_id);
create index if not exists idx_events_user_id on events(user_id);

-- ─────────────────────────────────────────────────────────────
-- Helper functions for RLS
-- ─────────────────────────────────────────────────────────────
create or replace function public.is_household_member(h_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select exists (
        select 1
        from household_members hm
        where hm.household_id = h_id
          and hm.user_id = auth.uid()
    );
$$;

create or replace function public.can_read_record(
    row_user_id uuid,
    row_household_id uuid,
    row_visibility text
)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select
        (row_visibility = 'private' and row_user_id = auth.uid())
        or (
            row_visibility = 'household'
            and row_household_id is not null
            and public.is_household_member(row_household_id)
        );
$$;

create or replace function public.can_write_record(
    row_user_id uuid,
    row_household_id uuid,
    row_visibility text
)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
    select
        (row_visibility = 'private' and row_user_id = auth.uid())
        or (
            row_visibility = 'household'
            and row_household_id is not null
            and public.is_household_member(row_household_id)
        );
$$;

-- ─────────────────────────────────────────────────────────────
-- Enable RLS
-- ─────────────────────────────────────────────────────────────
alter table households enable row level security;
alter table household_members enable row level security;
alter table user_profiles enable row level security;
alter table assets enable row level security;
alter table projects enable row level security;
alter table tasks enable row level security;
alter table documents enable row level security;
alter table decisions enable row level security;
alter table events enable row level security;
alter table inbox_items enable row level security;
alter table memory_items enable row level security;
alter table requests_log enable row level security;
alter table chat_history enable row level security;

-- ─────────────────────────────────────────────────────────────
-- RLS: households
-- ─────────────────────────────────────────────────────────────
drop policy if exists households_select on households;
create policy households_select on households
    for select to authenticated
    using (public.is_household_member(id) or created_by = auth.uid());

drop policy if exists households_insert on households;
create policy households_insert on households
    for insert to authenticated
    with check (created_by = auth.uid());

drop policy if exists households_update on households;
create policy households_update on households
    for update to authenticated
    using (created_by = auth.uid());

-- ─────────────────────────────────────────────────────────────
-- RLS: household_members
-- ─────────────────────────────────────────────────────────────
drop policy if exists household_members_select on household_members;
create policy household_members_select on household_members
    for select to authenticated
    using (user_id = auth.uid() or public.is_household_member(household_id));

drop policy if exists household_members_insert on household_members;
create policy household_members_insert on household_members
    for insert to authenticated
    with check (user_id = auth.uid() or public.is_household_member(household_id));

-- ─────────────────────────────────────────────────────────────
-- RLS: user_profiles
-- ─────────────────────────────────────────────────────────────
drop policy if exists user_profiles_select on user_profiles;
create policy user_profiles_select on user_profiles
    for select to authenticated
    using (id = auth.uid());

drop policy if exists user_profiles_insert on user_profiles;
create policy user_profiles_insert on user_profiles
    for insert to authenticated
    with check (id = auth.uid());

drop policy if exists user_profiles_update on user_profiles;
create policy user_profiles_update on user_profiles
    for update to authenticated
    using (id = auth.uid());

-- ─────────────────────────────────────────────────────────────
-- RLS macro for data tables
-- ─────────────────────────────────────────────────────────────
do $$
declare
    tbl text;
begin
    foreach tbl in array array[
        'assets', 'projects', 'tasks', 'documents', 'decisions',
        'events', 'inbox_items', 'memory_items', 'requests_log', 'chat_history'
    ]
    loop
        execute format('drop policy if exists %I_select on %I', tbl, tbl);
        execute format(
            'create policy %I_select on %I for select to authenticated using (
                public.can_read_record(user_id, household_id, visibility)
            )',
            tbl, tbl
        );

        execute format('drop policy if exists %I_insert on %I', tbl, tbl);
        execute format(
            'create policy %I_insert on %I for insert to authenticated with check (
                user_id = auth.uid()
                and (
                    (visibility = ''private'' and household_id is null)
                    or (
                        visibility = ''household''
                        and household_id is not null
                        and public.is_household_member(household_id)
                    )
                )
            )',
            tbl, tbl
        );

        execute format('drop policy if exists %I_update on %I', tbl, tbl);
        execute format(
            'create policy %I_update on %I for update to authenticated using (
                public.can_write_record(user_id, household_id, visibility)
            ) with check (
                user_id = auth.uid()
                and (
                    (visibility = ''private'' and household_id is null)
                    or (
                        visibility = ''household''
                        and household_id is not null
                        and public.is_household_member(household_id)
                    )
                )
            )',
            tbl, tbl
        );

        execute format('drop policy if exists %I_delete on %I', tbl, tbl);
        execute format(
            'create policy %I_delete on %I for delete to authenticated using (
                public.can_write_record(user_id, household_id, visibility)
            )',
            tbl, tbl
        );
    end loop;
end $$;

-- ─────────────────────────────────────────────────────────────
-- Storage policies for documents bucket
-- Paths:
--   household/{household_id}/{module}/...
--   private/{user_id}/{module}/...
-- ─────────────────────────────────────────────────────────────
-- Ensure bucket exists manually in Dashboard if not already created.

drop policy if exists documents_household_read on storage.objects;
create policy documents_household_read on storage.objects
    for select to authenticated
    using (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'household'
        and public.is_household_member(((storage.foldername(name))[2])::uuid)
    );

drop policy if exists documents_private_read on storage.objects;
create policy documents_private_read on storage.objects
    for select to authenticated
    using (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'private'
        and (storage.foldername(name))[2] = auth.uid()::text
    );

drop policy if exists documents_household_insert on storage.objects;
create policy documents_household_insert on storage.objects
    for insert to authenticated
    with check (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'household'
        and public.is_household_member(((storage.foldername(name))[2])::uuid)
    );

drop policy if exists documents_private_insert on storage.objects;
create policy documents_private_insert on storage.objects
    for insert to authenticated
    with check (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'private'
        and (storage.foldername(name))[2] = auth.uid()::text
    );

drop policy if exists documents_household_delete on storage.objects;
create policy documents_household_delete on storage.objects
    for delete to authenticated
    using (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'household'
        and public.is_household_member(((storage.foldername(name))[2])::uuid)
    );

drop policy if exists documents_private_delete on storage.objects;
create policy documents_private_delete on storage.objects
    for delete to authenticated
    using (
        bucket_id = 'documents'
        and (storage.foldername(name))[1] = 'private'
        and (storage.foldername(name))[2] = auth.uid()::text
    );
