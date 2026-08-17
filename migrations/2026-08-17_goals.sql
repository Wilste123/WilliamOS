-- Goals table for Priority Engine and Minne-adjacent UI
-- Prerequisite: migrations/2026-08-16_auth_households.sql (households + RLS helpers)
-- Idempotent: safe to run multiple times.

create table if not exists goals (
    id          uuid primary key default uuid_generate_v4(),
    title       text not null,
    description text,
    status      text not null default 'active'
                    check (status in ('active', 'paused', 'completed')),
    next_step   text,
    target_date timestamptz,
    progress    integer not null default 0 check (progress >= 0 and progress <= 100),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz
);

alter table goals add column if not exists user_id uuid references auth.users(id) on delete set null;
alter table goals add column if not exists household_id uuid references households(id) on delete set null;
alter table goals add column if not exists visibility text not null default 'household';
alter table goals drop constraint if exists goals_visibility_check;
alter table goals add constraint goals_visibility_check check (visibility in ('private', 'household'));

create index if not exists idx_goals_status on goals(status);
create index if not exists idx_goals_household_id on goals(household_id);
create index if not exists idx_goals_user_id on goals(user_id);

alter table goals enable row level security;

drop policy if exists goals_select on goals;
create policy goals_select on goals
    for select to authenticated
    using (public.can_read_record(user_id, household_id, visibility));

drop policy if exists goals_insert on goals;
create policy goals_insert on goals
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

drop policy if exists goals_update on goals;
create policy goals_update on goals
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

drop policy if exists goals_delete on goals;
create policy goals_delete on goals
    for delete to authenticated
    using (public.can_write_record(user_id, household_id, visibility));
