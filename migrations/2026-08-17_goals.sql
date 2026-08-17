-- Goals table for Priority Engine and Minne-adjacent UI
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

create index if not exists idx_goals_status on goals(status);
