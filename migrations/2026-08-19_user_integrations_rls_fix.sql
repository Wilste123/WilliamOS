-- Fix user_integrations RLS so authenticated inserts work via PostgREST.
-- Align with usage_log policies (no "to authenticated" role clause).

drop policy if exists user_integrations_select on user_integrations;
create policy user_integrations_select on user_integrations
    for select using (auth.uid() = user_id);

drop policy if exists user_integrations_insert on user_integrations;
create policy user_integrations_insert on user_integrations
    for insert with check (auth.uid() = user_id);

drop policy if exists user_integrations_update on user_integrations;
create policy user_integrations_update on user_integrations
    for update
    using (auth.uid() = user_id)
    with check (auth.uid() = user_id);

drop policy if exists user_integrations_delete on user_integrations;
create policy user_integrations_delete on user_integrations
    for delete using (auth.uid() = user_id);
