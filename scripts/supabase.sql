-- Housing Comps: accounts, saved searches, contributions, activity log.
-- Run once in Supabase: SQL Editor -> New query -> paste this file -> Run.
-- Safe to re-run (drops and recreates policies; tables are created only if missing).

-- ---------- tables ----------
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  email text,
  name text,
  alias text,
  company text,
  role text,
  linkedin text,
  is_admin boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.saved_searches (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users on delete cascade,
  name text not null,
  state jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.contributions (
  id bigint generated always as identity primary key,
  user_id uuid not null default auth.uid() references auth.users on delete cascade,
  record_id text,
  topic text,
  source_url text,
  details text,
  public_ok boolean not null default false,
  credit_as text,
  status text not null default 'new' check (status in ('new', 'accepted', 'declined', 'entered')),
  admin_note text,
  created_at timestamptz not null default now()
);

create table if not exists public.activity (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users on delete set null,
  session_id text,
  event text not null,
  detail jsonb,
  page text,
  created_at timestamptz not null default now()
);
create index if not exists activity_created_idx on public.activity (created_at desc);
create index if not exists activity_user_idx on public.activity (user_id);

-- ---------- admin check (security definer avoids recursive policy lookups) ----------
create or replace function public.is_admin() returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select is_admin from public.profiles where id = auth.uid()), false)
$$;

-- ---------- new sign-up -> profile row (fields come from the sign-up form) ----------
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, name, alias, company, role)
  values (new.id, new.email,
          new.raw_user_meta_data->>'name', new.raw_user_meta_data->>'alias',
          new.raw_user_meta_data->>'company', new.raw_user_meta_data->>'role')
  on conflict (id) do nothing;
  return new;
end $$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- users may not promote themselves (the SQL editor has no auth.uid(), so the owner can still set it there)
create or replace function public.keep_admin_flag() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is not null and not public.is_admin() then new.is_admin := old.is_admin; end if;
  return new;
end $$;
drop trigger if exists profiles_keep_admin on public.profiles;
create trigger profiles_keep_admin before update on public.profiles
  for each row execute function public.keep_admin_flag();

-- ---------- row level security ----------
alter table public.profiles enable row level security;
alter table public.saved_searches enable row level security;
alter table public.contributions enable row level security;
alter table public.activity enable row level security;

drop policy if exists "own profile read" on public.profiles;
drop policy if exists "own profile update" on public.profiles;
create policy "own profile read" on public.profiles for select to authenticated using (id = auth.uid() or public.is_admin());
create policy "own profile update" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists "own searches" on public.saved_searches;
create policy "own searches" on public.saved_searches for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "submit contribution" on public.contributions;
drop policy if exists "read contributions" on public.contributions;
drop policy if exists "admin moderates" on public.contributions;
create policy "submit contribution" on public.contributions for insert to authenticated with check (user_id = auth.uid());
create policy "read contributions" on public.contributions for select to authenticated using (user_id = auth.uid() or public.is_admin());
create policy "admin moderates" on public.contributions for update to authenticated using (public.is_admin());

-- anyone may add activity rows (signed-in rows must carry their own id); only the admin reads them
drop policy if exists "log activity" on public.activity;
drop policy if exists "admin reads activity" on public.activity;
create policy "log activity" on public.activity for insert to anon, authenticated
  with check (user_id is null or user_id = auth.uid());
create policy "admin reads activity" on public.activity for select to authenticated using (public.is_admin());

-- ---------- grants (new tables are not exposed automatically in this project) ----------
grant usage on schema public to anon, authenticated;
grant select, update on public.profiles to authenticated;
grant select, insert, update, delete on public.saved_searches to authenticated;
grant select, insert, update on public.contributions to authenticated;
grant insert on public.activity to anon, authenticated;
grant select on public.activity to authenticated;
grant execute on function public.is_admin() to anon, authenticated;

-- ---------- after you create your own account on the site, run this once ----------
-- update public.profiles set is_admin = true where email = 'paul@montarav.com';
