-- WilliamOS Unified Storage Migration
-- Run in Supabase SQL editor or via psql.
-- Idempotent: safe to run multiple times.
-- Generated: 2026-08-13

-- ─────────────────────────────────────────────────────────────
-- Extensions
-- ─────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ─────────────────────────────────────────────────────────────
-- assets
-- ─────────────────────────────────────────────────────────────
create table if not exists assets (
    id          uuid primary key default uuid_generate_v4(),
    name        text not null,
    type        text,
    status      text not null default 'active'
                    check (status in ('active', 'considering_purchase', 'inactive')),
    description text,
    estimated_value numeric,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

-- Add columns that may be missing from an earlier schema version
alter table assets add column if not exists status text not null default 'active';
alter table assets add column if not exists estimated_value numeric;
alter table assets add column if not exists updated_at timestamptz;

-- ─────────────────────────────────────────────────────────────
-- projects
-- ─────────────────────────────────────────────────────────────
create table if not exists projects (
    id          uuid primary key default uuid_generate_v4(),
    name        text not null,
    status      text not null default 'active'
                    check (status in ('active', 'on_hold', 'done')),
    next_action text,
    notes       text,
    asset_id    uuid references assets(id) on delete set null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

alter table projects add column if not exists asset_id uuid references assets(id) on delete set null;
alter table projects add column if not exists updated_at timestamptz;

-- ─────────────────────────────────────────────────────────────
-- tasks
-- ─────────────────────────────────────────────────────────────
create table if not exists tasks (
    id          uuid primary key default uuid_generate_v4(),
    title       text not null,
    description text,
    due_date    timestamptz,
    priority    integer not null default 2 check (priority in (1, 2, 3)),
    status      text not null default 'open'
                    check (status in ('open', 'in_progress', 'completed')),
    completed   boolean not null default false,
    asset_id    uuid references assets(id) on delete set null,
    project_id  uuid references projects(id) on delete set null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

alter table tasks add column if not exists description text;
alter table tasks add column if not exists status text not null default 'open';
alter table tasks add column if not exists updated_at timestamptz;

-- ─────────────────────────────────────────────────────────────
-- documents
-- ─────────────────────────────────────────────────────────────
create table if not exists documents (
    id            uuid primary key default uuid_generate_v4(),
    filename      text not null,
    storage_path  text,
    text_content  text,
    source_module text,
    asset_id      uuid references assets(id) on delete set null,
    project_id    uuid references projects(id) on delete set null,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz
);

-- Rename uploaded_at → created_at if the old column exists (idempotent guard)
do $$
begin
    if exists (
        select 1 from information_schema.columns
        where table_name = 'documents' and column_name = 'uploaded_at'
    ) and not exists (
        select 1 from information_schema.columns
        where table_name = 'documents' and column_name = 'created_at'
    ) then
        alter table documents rename column uploaded_at to created_at;
    end if;
end
$$;

alter table documents add column if not exists text_content  text;
alter table documents add column if not exists source_module text;
alter table documents add column if not exists updated_at    timestamptz;

-- ─────────────────────────────────────────────────────────────
-- decisions
-- ─────────────────────────────────────────────────────────────
create table if not exists decisions (
    id          uuid primary key default uuid_generate_v4(),
    title       text not null,
    summary     text,
    status      text not null default 'open'
                    check (status in ('open', 'decided', 'paused')),
    decided_at  timestamptz,
    asset_id    uuid references assets(id) on delete set null,
    project_id  uuid references projects(id) on delete set null,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

-- ─────────────────────────────────────────────────────────────
-- events (audit / timeline)
-- ─────────────────────────────────────────────────────────────
create table if not exists events (
    id          uuid primary key default uuid_generate_v4(),
    title       text not null,
    event_type  text,
    notes       text,
    event_date  timestamptz,
    asset_id    uuid references assets(id) on delete set null,
    project_id  uuid references projects(id) on delete set null,
    decision_id uuid references decisions(id) on delete set null,
    created_at  timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- inbox_items
-- ─────────────────────────────────────────────────────────────
create table if not exists inbox_items (
    id          uuid primary key default uuid_generate_v4(),
    text        text not null,
    status      text not null default 'captured',
    suggestions jsonb,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

-- ─────────────────────────────────────────────────────────────
-- memory_items (existing table — add missing columns)
-- ─────────────────────────────────────────────────────────────
create table if not exists memory_items (
    id         uuid primary key default uuid_generate_v4(),
    key        text,
    value      text not null,
    category   text,
    created_at timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- chat_history (existing table — preserved as-is)
-- ─────────────────────────────────────────────────────────────
create table if not exists chat_history (
    id         uuid primary key default uuid_generate_v4(),
    role       text not null,
    content    text not null,
    created_at timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- requests_log (existing table — preserved as-is)
-- ─────────────────────────────────────────────────────────────
create table if not exists requests_log (
    id               uuid primary key default uuid_generate_v4(),
    request_text     text not null,
    category         text,
    suggested_module text,
    created_at       timestamptz not null default now()
);

-- ─────────────────────────────────────────────────────────────
-- Indexes for common query patterns
-- ─────────────────────────────────────────────────────────────
create index if not exists idx_tasks_asset_id      on tasks(asset_id);
create index if not exists idx_tasks_project_id    on tasks(project_id);
create index if not exists idx_tasks_status        on tasks(status);
create index if not exists idx_projects_status     on projects(status);
create index if not exists idx_documents_asset_id  on documents(asset_id);
create index if not exists idx_documents_project_id on documents(project_id);
create index if not exists idx_decisions_status    on decisions(status);
create index if not exists idx_events_asset_id     on events(asset_id);
create index if not exists idx_events_project_id   on events(project_id);
create index if not exists idx_events_event_type   on events(event_type);
