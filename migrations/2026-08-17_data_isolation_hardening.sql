-- Data isolation hardening: backfill orphan rows, inbox columns, health_metrics RLS fix
-- Prerequisite: all prior migrations including 2026-08-17_finance_health_integrations.sql
-- Idempotent: safe to run multiple times.

-- ─────────────────────────────────────────────────────────────
-- inbox_items: document signal columns used by the app
-- ─────────────────────────────────────────────────────────────
alter table inbox_items add column if not exists signal_type text;
alter table inbox_items add column if not exists document_id uuid;
alter table inbox_items add column if not exists doc_type text;

-- ─────────────────────────────────────────────────────────────
-- Ensure auth columns exist on newer tables
-- ─────────────────────────────────────────────────────────────
do $$
declare
    tbl text;
begin
    foreach tbl in array array[
        'goals', 'finance_accounts', 'finance_snapshots', 'health_metrics', 'usage_log'
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

alter table health_metrics alter column visibility set default 'private';
alter table usage_log alter column visibility set default 'private';

-- ─────────────────────────────────────────────────────────────
-- Backfill orphan rows so RLS can scope them correctly
-- ─────────────────────────────────────────────────────────────
do $$
declare
    tbl text;
begin
    foreach tbl in array array[
        'assets', 'projects', 'tasks', 'documents', 'decisions', 'events',
        'inbox_items', 'memory_items', 'requests_log', 'chat_history', 'goals',
        'finance_accounts', 'finance_snapshots', 'health_metrics'
    ]
    loop
        -- Household rows missing owner: assign household owner
        execute format($sql$
            update %I target
            set user_id = hm.user_id
            from household_members hm
            where target.user_id is null
              and target.household_id is not null
              and hm.household_id = target.household_id
              and hm.role = 'owner'
        $sql$, tbl);

        -- Household rows missing household_id: use owner's default household
        execute format($sql$
            update %I target
            set household_id = up.default_household_id,
                user_id = coalesce(target.user_id, up.id)
            from user_profiles up
            where target.household_id is null
              and target.visibility = 'household'
              and target.user_id = up.id
              and up.default_household_id is not null
        $sql$, tbl);

        -- Private rows missing user_id: cannot infer owner — leave invisible (RLS safe)
    end loop;
end $$;

-- ─────────────────────────────────────────────────────────────
-- health_metrics: align update policy with other data tables
-- ─────────────────────────────────────────────────────────────
drop policy if exists health_metrics_update on health_metrics;
create policy health_metrics_update on health_metrics
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

drop policy if exists health_metrics_delete on health_metrics;
create policy health_metrics_delete on health_metrics
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));

-- ─────────────────────────────────────────────────────────────
-- usage_log: explicit authenticated role on policies
-- ─────────────────────────────────────────────────────────────
drop policy if exists usage_log_select on usage_log;
create policy usage_log_select on usage_log
    for select to authenticated
    using (auth.uid() = user_id);

drop policy if exists usage_log_insert on usage_log;
create policy usage_log_insert on usage_log
    for insert to authenticated
    with check (auth.uid() = user_id);

drop policy if exists usage_log_delete on usage_log;
create policy usage_log_delete on usage_log
    for delete to authenticated
    using (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────
-- finance_snapshots: allow delete for record owner / household
-- ─────────────────────────────────────────────────────────────
drop policy if exists finance_snapshots_delete on finance_snapshots;
create policy finance_snapshots_delete on finance_snapshots
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));

-- ─────────────────────────────────────────────────────────────
-- household_members: only owners may add members
-- ─────────────────────────────────────────────────────────────
drop policy if exists household_members_insert on household_members;
create policy household_members_insert on household_members
    for insert to authenticated
    with check (
        user_id = auth.uid()
        or exists (
            select 1
            from household_members existing
            where existing.household_id = household_members.household_id
              and existing.user_id = auth.uid()
              and existing.role = 'owner'
        )
    );
