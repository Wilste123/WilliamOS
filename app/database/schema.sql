-- WilliamOS starter schema
-- Run this in Supabase SQL editor when ready.

create extension if not exists "uuid-ossp";

create table if not exists assets (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    type text,
    description text,
    created_at timestamp with time zone default now()
);

create table if not exists projects (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    status text default 'active',
    next_action text,
    notes text,
    created_at timestamp with time zone default now()
);

create table if not exists tasks (
    id uuid primary key default uuid_generate_v4(),
    title text not null,
    due_date timestamp with time zone,
    priority integer default 2,
    completed boolean default false,
    asset_id uuid references assets(id) on delete set null,
    project_id uuid references projects(id) on delete set null,
    created_at timestamp with time zone default now()
);

create table if not exists documents (
    id uuid primary key default uuid_generate_v4(),
    filename text not null,
    storage_path text,
    asset_id uuid references assets(id) on delete set null,
    project_id uuid references projects(id) on delete set null,
    uploaded_at timestamp with time zone default now()
);

create table if not exists memory_items (
    id uuid primary key default uuid_generate_v4(),
    key text,
    value text not null,
    category text,
    created_at timestamp with time zone default now()
);

create table if not exists chat_history (
    id uuid primary key default uuid_generate_v4(),
    role text not null,
    content text not null,
    created_at timestamp with time zone default now()
);

create table if not exists requests_log (
    id uuid primary key default uuid_generate_v4(),
    request_text text not null,
    category text,
    suggested_module text,
    created_at timestamp with time zone default now()
);
