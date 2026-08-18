-- Add Google as an integration provider (Calendar + Gmail)

alter table user_integrations drop constraint if exists user_integrations_provider_check;

alter table user_integrations add constraint user_integrations_provider_check
    check (provider in ('google', 'outlook', 'apple_health', 'garmin', 'strava'));
