-- Memory provenance + user preferences for settings
-- Idempotent: safe to run multiple times.

alter table memory_items add column if not exists source text;

alter table user_profiles add column if not exists preferences jsonb not null default '{}'::jsonb;

create index if not exists idx_memory_items_source on memory_items(source);
