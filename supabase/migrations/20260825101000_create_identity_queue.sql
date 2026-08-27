create extension if not exists citext with schema extensions;

create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete restrict,
  full_name text not null check (length(btrim(full_name)) >= 2),
  email extensions.citext not null unique,
  role text not null constraint profiles_role_check check (role in ('admin', 'seller')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.seller_queue (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  position smallint not null unique check (position between 1 and 4),
  is_paused boolean not null default false,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.queue_state (
  singleton boolean primary key default true check (singleton = true),
  next_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  version bigint not null default 0 check (version >= 0),
  updated_at timestamptz not null default now()
);

create table public.seller_skip_balances (
  seller_id uuid primary key references public.profiles(user_id) on delete restrict,
  balance integer not null default 0 check (balance >= 0),
  updated_at timestamptz not null default now()
);

create index seller_queue_position_idx on public.seller_queue(position);
create index seller_skip_balances_balance_idx on public.seller_skip_balances(balance);

create or replace function private.current_user_role()
returns text
language sql stable security definer
set search_path = ''
as $$
  select p.role
  from public.profiles p
  where p.user_id = (select auth.uid())
    and p.is_active = true;
$$;

create or replace function private.is_admin()
returns boolean
language sql stable security definer
set search_path = ''
as $$ select coalesce((select private.current_user_role()) = 'admin', false); $$;

create or replace function private.is_current_seller(target_seller_id uuid)
returns boolean
language sql stable security definer
set search_path = ''
as $$
  select target_seller_id = (select auth.uid())
    and (select private.current_user_role()) = 'seller';
$$;

revoke all on function private.current_user_role() from public, anon, authenticated, service_role;
revoke all on function private.is_admin() from public, anon, authenticated, service_role;
revoke all on function private.is_current_seller(uuid) from public, anon, authenticated, service_role;

revoke all on public.profiles, public.seller_queue, public.queue_state,
  public.seller_skip_balances from public, anon, authenticated;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances
  to authenticated;
