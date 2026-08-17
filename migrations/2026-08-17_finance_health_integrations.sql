-- Finance, Health metrics, and external integrations (Outlook, Garmin, etc.)
-- Prerequisite: migrations/2026-08-16_auth_households.sql
-- Idempotent: safe to run multiple times.

-- ─────────────────────────────────────────────────────────────
-- finance_accounts
-- ─────────────────────────────────────────────────────────────
create table if not exists finance_accounts (
    id            uuid primary key default uuid_generate_v4(),
    name          text not null,
    account_type  text not null default 'asset'
                      check (account_type in ('asset', 'debt', 'liquidity')),
    balance_nok   numeric not null default 0,
    institution   text,
    notes         text,
    user_id       uuid references auth.users(id) on delete set null,
    household_id  uuid references households(id) on delete set null,
    visibility    text not null default 'household'
                      check (visibility in ('private', 'household')),
    created_at    timestamptz not null default now(),
    updated_at    timestamptz
);

create index if not exists idx_finance_accounts_household_id on finance_accounts(household_id);
create index if not exists idx_finance_accounts_user_id on finance_accounts(user_id);

alter table finance_accounts enable row level security;

drop policy if exists finance_accounts_select on finance_accounts;
create policy finance_accounts_select on finance_accounts
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists finance_accounts_insert on finance_accounts;
create policy finance_accounts_insert on finance_accounts
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

drop policy if exists finance_accounts_update on finance_accounts;
create policy finance_accounts_update on finance_accounts
    for update to authenticated
    using (public.can_write_record(user_id, household_id, visibility))
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

drop policy if exists finance_accounts_delete on finance_accounts;
create policy finance_accounts_delete on finance_accounts
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));

-- ─────────────────────────────────────────────────────────────
-- finance_snapshots (monthly net worth history)
-- ─────────────────────────────────────────────────────────────
create table if not exists finance_snapshots (
    id             uuid primary key default uuid_generate_v4(),
    net_worth_nok  numeric not null,
    recorded_at    timestamptz not null default now(),
    user_id        uuid references auth.users(id) on delete set null,
    household_id   uuid references households(id) on delete set null,
    visibility     text not null default 'household'
                       check (visibility in ('private', 'household')),
    created_at     timestamptz not null default now()
);

create index if not exists idx_finance_snapshots_household_id on finance_snapshots(household_id);
create index if not exists idx_finance_snapshots_recorded_at on finance_snapshots(recorded_at desc);

alter table finance_snapshots enable row level security;

drop policy if exists finance_snapshots_select on finance_snapshots;
create policy finance_snapshots_select on finance_snapshots
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists finance_snapshots_insert on finance_snapshots;
create policy finance_snapshots_insert on finance_snapshots
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

-- ─────────────────────────────────────────────────────────────
-- health_metrics
-- ─────────────────────────────────────────────────────────────
create table if not exists health_metrics (
    id           uuid primary key default uuid_generate_v4(),
    metric_type  text not null
                     check (metric_type in ('weight', 'sleep_hours', 'activity_minutes', 'steps')),
    value        numeric not null,
    unit         text,
    source       text not null default 'manual'
                     check (source in ('manual', 'apple_health', 'garmin', 'strava')),
    recorded_at  timestamptz not null default now(),
    notes        text,
    user_id      uuid references auth.users(id) on delete set null,
    household_id uuid references households(id) on delete set null,
    visibility   text not null default 'private'
                     check (visibility in ('private', 'household')),
    created_at   timestamptz not null default now()
);

create index if not exists idx_health_metrics_user_id on health_metrics(user_id);
create index if not exists idx_health_metrics_type_recorded on health_metrics(metric_type, recorded_at desc);

alter table health_metrics enable row level security;

drop policy if exists health_metrics_select on health_metrics;
create policy health_metrics_select on health_metrics
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists health_metrics_insert on health_metrics;
create policy health_metrics_insert on health_metrics
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

drop policy if exists health_metrics_update on health_metrics;
create policy health_metrics_update on health_metrics
    for update to authenticated
    using (public.can_write_record(user_id, household_id, visibility))
    with check (user_id = auth.uid());

drop policy if exists health_metrics_delete on health_metrics;
create policy health_metrics_delete on health_metrics
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));

-- ─────────────────────────────────────────────────────────────
-- user_integrations (Outlook, Apple Health, Garmin, Strava)
-- ─────────────────────────────────────────────────────────────
create table if not exists user_integrations (
    id               uuid primary key default uuid_generate_v4(),
    provider         text not null
                         check (provider in ('outlook', 'apple_health', 'garmin', 'strava')),
    status           text not null default 'disconnected'
                         check (status in ('disconnected', 'pending', 'connected', 'error')),
    access_token     text,
    refresh_token    text,
    token_expires_at timestamptz,
    metadata         jsonb not null default '{}'::jsonb,
    last_sync_at     timestamptz,
    user_id          uuid not null references auth.users(id) on delete cascade,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz,
    unique (user_id, provider)
);

create index if not exists idx_user_integrations_user_id on user_integrations(user_id);

alter table user_integrations enable row level security;

drop policy if exists user_integrations_select on user_integrations;
create policy user_integrations_select on user_integrations
    for select to authenticated
    using (user_id = auth.uid());

drop policy if exists user_integrations_insert on user_integrations;
create policy user_integrations_insert on user_integrations
    for insert to authenticated
    with check (user_id = auth.uid());

drop policy if exists user_integrations_update on user_integrations;
create policy user_integrations_update on user_integrations
    for update to authenticated
    using (user_id = auth.uid())
    with check (user_id = auth.uid());

drop policy if exists user_integrations_delete on user_integrations;
create policy user_integrations_delete on user_integrations
    for delete to authenticated
    using (user_id = auth.uid());
