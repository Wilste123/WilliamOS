-- Quarantine legacy rows without ownership and re-assert RLS on data tables.
-- Run after 2026-08-17_data_isolation_hardening.sql
-- Idempotent: safe to run multiple times.

-- Legacy rows created before auth could be readable when RLS was missing.
-- Make ownerless rows private so no household can claim them.
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
        execute format($sql$
            update %I
            set visibility = 'private',
                household_id = null
            where user_id is null
              and household_id is null
        $sql$, tbl);
    end loop;
end $$;

-- Re-enable RLS in case an earlier migration was skipped.
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
alter table goals enable row level security;
alter table finance_accounts enable row level security;
alter table finance_snapshots enable row level security;
alter table health_metrics enable row level security;
alter table usage_log enable row level security;
alter table user_integrations enable row level security;
