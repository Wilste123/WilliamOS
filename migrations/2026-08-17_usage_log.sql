-- Usage log for 7-day daily-use validation
create table if not exists usage_log (
    id         uuid primary key default uuid_generate_v4(),
    opened_on  date not null,
    user_id    uuid references auth.users(id) on delete cascade,
    household_id uuid references households(id) on delete cascade,
    visibility text not null default 'private',
    created_at timestamptz not null default now(),
    unique (user_id, opened_on)
);

create index if not exists idx_usage_log_opened_on on usage_log(opened_on desc);

alter table usage_log enable row level security;

create policy usage_log_select on usage_log
    for select using (auth.uid() = user_id);

create policy usage_log_insert on usage_log
    for insert with check (auth.uid() = user_id);

create policy usage_log_delete on usage_log
    for delete using (auth.uid() = user_id);
