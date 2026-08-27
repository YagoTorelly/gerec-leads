create table public.assignments (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  assignment_type text not null check (assignment_type in ('normal', 'recurring', 'temporary', 'permanent_transfer')),
  started_at timestamptz not null default now(), ended_at timestamptz,
  actor_id uuid references public.profiles(user_id) on delete restrict, reason text,
  idempotency_key text not null unique,
  check (ended_at is null or ended_at >= started_at)
);
create unique index assignments_current_lead_uq on public.assignments(lead_id) where ended_at is null;
create index assignments_seller_idx on public.assignments(seller_id, started_at, ended_at);
create index assignments_lead_idx on public.assignments(lead_id, started_at);

create table public.feedback_cycles (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  cycle_number integer not null check (cycle_number >= 1), starts_at timestamptz not null,
  reminder_at timestamptz not null, due_at timestamptz not null, closed_at timestamptz, close_reason text,
  unique (lead_id, cycle_number), check (reminder_at <= due_at), check (closed_at is null or closed_at >= starts_at)
);
create unique index feedback_cycles_open_lead_uq on public.feedback_cycles(lead_id) where closed_at is null;
create index feedback_cycles_due_idx on public.feedback_cycles(due_at) where closed_at is null;

create table public.feedbacks (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6), contact_started boolean not null check (contact_started),
  idempotency_key text not null unique, created_at timestamptz not null default now()
);
create index feedbacks_lead_idx on public.feedbacks(lead_id, created_at);

create table public.contact_attempts (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  seller_id uuid not null references public.profiles(user_id) on delete restrict,
  channel text not null check (channel = 'whatsapp'), business_date date not null,
  comment text not null check (length(btrim(comment)) >= 6), idempotency_key text not null unique,
  created_at timestamptz not null default now(), unique (lead_id, business_date)
);
create index contact_attempts_lead_idx on public.contact_attempts(lead_id, business_date);

create table public.qualification_events (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  assignment_id bigint not null references public.assignments(id) on delete restrict,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  outcome text not null check (outcome in ('qualified_follow_up', 'qualified_closed_no_conversion', 'disqualified', 'won', 'reversed')),
  reason text check (reason is null or reason in ('no_answer_after_five_attempts', 'no_cnpj', 'outside_sp')),
  comment text not null check (length(btrim(comment)) >= 6), idempotency_key text not null unique,
  reversed_event_id bigint references public.qualification_events(id) on delete restrict,
  created_at timestamptz not null default now(), check ((outcome = 'disqualified' and reason is not null) or outcome <> 'disqualified')
);
create index qualification_events_lead_idx on public.qualification_events(lead_id, created_at);

create table public.sales (
  id bigint generated always as identity primary key,
  lead_id bigint not null references public.leads(id) on delete restrict,
  credited_seller_id uuid not null references public.profiles(user_id) on delete restrict,
  qualification_event_id bigint not null unique references public.qualification_events(id) on delete restrict,
  comment text not null check (length(btrim(comment)) >= 6), won_at timestamptz not null default now(),
  reversed_at timestamptz, reversed_by uuid references public.profiles(user_id) on delete restrict
);
create unique index sales_active_lead_uq on public.sales(lead_id) where reversed_at is null;
create index sales_credited_seller_idx on public.sales(credited_seller_id, won_at);

create table public.business_holidays (
  holiday_date date not null, scope text not null check (scope in ('national', 'sp')),
  name text not null check (length(btrim(name)) > 0), primary key (holiday_date, scope)
);

create table public.notification_outbox (
  id uuid primary key default gen_random_uuid(), event_type text not null, aggregate_type text not null, aggregate_id text not null,
  idempotency_key text not null unique, payload jsonb not null,
  status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'failed')),
  attempts integer not null default 0 check (attempts >= 0), available_at timestamptz not null default now(), last_error text,
  created_at timestamptz not null default now(), processed_at timestamptz
);
create index notification_outbox_pending_idx on public.notification_outbox(status, available_at);

create table public.notification_incidents (
  id uuid primary key default gen_random_uuid(), incident_type text not null check (incident_type = 'parked_threshold'),
  opened_at timestamptz not null default now(), resolved_at timestamptz
);
create unique index notification_incidents_open_uq on public.notification_incidents(incident_type) where resolved_at is null;

create table public.audit_log (
  id bigint generated always as identity primary key, actor_id uuid references public.profiles(user_id) on delete restrict,
  action text not null, entity_type text not null, entity_id text not null, before_data jsonb, after_data jsonb,
  correlation_id uuid not null, created_at timestamptz not null default now()
);
create index audit_log_entity_idx on public.audit_log(entity_type, entity_id, created_at);

create table public.system_settings (
  singleton boolean primary key default true check (singleton = true), timezone text not null default 'America/Sao_Paulo',
  feedback_hours integer not null default 24 check (feedback_hours > 0), reminder_hours integer not null default 4 check (reminder_hours > 0 and reminder_hours < feedback_hours),
  parked_threshold integer not null default 2 check (parked_threshold >= 2), digest_time time not null default time '09:00:00', updated_at timestamptz not null default now()
);
