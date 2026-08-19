-- Semantic document search: store OpenAI embedding vectors as JSON arrays.
-- Run in Supabase SQL Editor after prior migrations.

alter table documents add column if not exists embedding jsonb;
alter table documents add column if not exists embedding_model text;
alter table documents add column if not exists embedded_at timestamptz;

create index if not exists idx_documents_embedded_at on documents(embedded_at);
