-- Goals module linking + project_links for many-to-many project associations
-- Prerequisite: migrations/2026-08-17_goals.sql, migrations/2026-08-16_auth_households.sql
-- Idempotent: safe to run multiple times.

-- ─────────────────────────────────────────────────────────────
-- goals: module + linked_id
-- ─────────────────────────────────────────────────────────────
alter table goals add column if not exists module text;
alter table goals add column if not exists linked_id uuid;

alter table goals drop constraint if exists goals_module_check;
alter table goals add constraint goals_module_check
    check (module is null or module in ('health', 'finance', 'asset', 'project', 'general'));

create index if not exists idx_goals_module on goals(module);
create index if not exists idx_goals_linked_id on goals(linked_id);

-- ─────────────────────────────────────────────────────────────
-- project_links
-- Core table first; auth columns added via ALTER so re-runs work when
-- an older/partial project_links table already exists without household_id.
-- ─────────────────────────────────────────────────────────────
create table if not exists project_links (
    id           uuid primary key default uuid_generate_v4(),
    project_id   uuid not null references projects(id) on delete cascade,
    entity_type  text not null,
    entity_id    uuid not null,
    created_at   timestamptz not null default now(),
    unique (project_id, entity_type, entity_id)
);

alter table project_links add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table project_links add column if not exists household_id uuid references households(id) on delete set null;
alter table project_links add column if not exists visibility text not null default 'household';

alter table project_links drop constraint if exists project_links_entity_type_check;
alter table project_links add constraint project_links_entity_type_check
    check (entity_type in ('asset', 'goal', 'document', 'finance_account', 'task', 'decision'));

alter table project_links drop constraint if exists project_links_visibility_check;
alter table project_links add constraint project_links_visibility_check
    check (visibility in ('private', 'household'));

create index if not exists idx_project_links_project_id on project_links(project_id);
create index if not exists idx_project_links_entity on project_links(entity_type, entity_id);
create index if not exists idx_project_links_household_id on project_links(household_id);

alter table project_links enable row level security;

drop policy if exists project_links_select on project_links;
create policy project_links_select on project_links
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists project_links_insert on project_links;
create policy project_links_insert on project_links
    for insert to authenticated
    with check (
        user_id = auth.uid()
        and (
            (visibility = 'private' and household_id is null)
            or (
                visibility = 'household'
                and household_id is not null
                and public.is_household_member(household_id)
            )
        )
    );

drop policy if exists project_links_delete on project_links;
create policy project_links_delete on project_links
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));
