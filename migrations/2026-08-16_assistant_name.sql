-- Add customizable assistant name to user profiles
-- Run in Supabase SQL editor after 2026-08-16_auth_households.sql

alter table user_profiles
    add column if not exists assistant_name text;

-- Optional: set a default for existing users
update user_profiles
set assistant_name = 'WilliamOS'
where assistant_name is null;
