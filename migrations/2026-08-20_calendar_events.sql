-- Calendar events: scheduled items (internal + Google sync)
-- Prerequisite: auth/household migrations
-- Idempotent: safe to run multiple times.

create table if not exists calendar_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade,
    household_id uuid references households(id) on delete set null,
    visibility text not null default 'household',
    title text not null,
    description text,
    location text,
    start_at timestamptz not null,
    end_at timestamptz,
    all_day boolean not null default false,
    source text not null default 'internal',
    external_id text,
    calendar_id text default 'primary',
    asset_id uuid references assets(id) on delete set null,
    project_id uuid references projects(id) on delete set null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table calendar_events add column if not exists user_id uuid references auth.users(id) on delete cascade;
alter table calendar_events add column if not exists household_id uuid references households(id) on delete set null;
alter table calendar_events add column if not exists visibility text not null default 'household';
alter table calendar_events add column if not exists description text;
alter table calendar_events add column if not exists location text;
alter table calendar_events add column if not exists end_at timestamptz;
alter table calendar_events add column if not exists all_day boolean not null default false;
alter table calendar_events add column if not exists source text not null default 'internal';
alter table calendar_events add column if not exists external_id text;
alter table calendar_events add column if not exists calendar_id text default 'primary';
alter table calendar_events add column if not exists asset_id uuid references assets(id) on delete set null;
alter table calendar_events add column if not exists project_id uuid references projects(id) on delete set null;
alter table calendar_events add column if not exists updated_at timestamptz not null default now();

alter table calendar_events drop constraint if exists calendar_events_visibility_check;
alter table calendar_events add constraint calendar_events_visibility_check
    check (visibility in ('private', 'household'));

alter table calendar_events drop constraint if exists calendar_events_source_check;
alter table calendar_events add constraint calendar_events_source_check
    check (source in ('internal', 'google'));

create unique index if not exists idx_calendar_events_google_unique
    on calendar_events(user_id, source, external_id)
    where external_id is not null;

create index if not exists idx_calendar_events_user_id on calendar_events(user_id);
create index if not exists idx_calendar_events_household_id on calendar_events(household_id);
create index if not exists idx_calendar_events_start_at on calendar_events(start_at);
create index if not exists idx_calendar_events_source on calendar_events(source);

alter table calendar_events enable row level security;

drop policy if exists calendar_events_select on calendar_events;
create policy calendar_events_select on calendar_events
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists calendar_events_insert on calendar_events;
create policy calendar_events_insert on calendar_events
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

drop policy if exists calendar_events_update on calendar_events;
create policy calendar_events_update on calendar_events
    for update to authenticated
    using (user_id = auth.uid());

drop policy if exists calendar_events_delete on calendar_events;
create policy calendar_events_delete on calendar_events
    for delete to authenticated
    using (user_id = auth.uid());
