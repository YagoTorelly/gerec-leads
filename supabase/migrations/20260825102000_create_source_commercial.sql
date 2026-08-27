create table public.import_runs (
  id uuid primary key default gen_random_uuid(),
  source_type text not null check (source_type in ('mock_workbook', 'google_sheets')),
  mode text not null check (mode in ('bootstrap', 'snapshot', 'incremental')),
  idempotency_key text not null unique,
  correlation_id uuid not null,
  status text not null check (status in ('running', 'completed', 'partial', 'failed')),
  rows_read integer not null default 0 check (rows_read >= 0),
  rows_created integer not null default 0 check (rows_created >= 0),
  rows_updated integer not null default 0 check (rows_updated >= 0),
  rows_ignored integer not null default 0 check (rows_ignored >= 0),
  rows_pending integer not null default 0 check (rows_pending >= 0),
  rows_failed integer not null default 0 check (rows_failed >= 0),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error_summary text
);

create table public.campaigns (
  id bigint generated always as identity primary key,
  external_id text,
  source_name text not null check (length(btrim(source_name)) > 0),
  display_name text not null check (length(btrim(display_name)) > 0),
  status text not null default 'pending_approval' check (status in ('pending_approval', 'approved', 'archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index campaigns_external_id_uq on public.campaigns(external_id) where external_id is not null;
create unique index campaigns_source_name_fallback_uq on public.campaigns((lower(btrim(source_name)))) where external_id is null;

create table public.companies (
  id bigint generated always as identity primary key,
  document_type text check (document_type in ('cpf', 'cnpj')),
  document_normalized text,
  document_display text,
  legal_name text,
  state text check (state is null or state ~ '^[A-Z]{2}$'),
  owner_id uuid references public.profiles(user_id) on delete restrict,
  client_since timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((document_type is null and document_normalized is null) or (document_type is not null and document_normalized is not null))
);
create unique index companies_document_uq on public.companies(document_normalized) where document_normalized is not null;
create index companies_owner_idx on public.companies(owner_id);

create table public.leads (
  id bigint generated always as identity primary key,
  company_id bigint not null references public.companies(id) on delete restrict,
  campaign_id bigint not null references public.campaigns(id) on delete restrict,
  source_entered_at timestamptz not null,
  assignment_status text not null default 'ready' check (assignment_status in ('ready', 'parked', 'assigned', 'archived')),
  qualification_status text not null default 'pending' check (qualification_status in ('pending', 'qualified', 'disqualified')),
  conversion_status text not null default 'active' check (conversion_status in ('active', 'qualified_follow_up', 'closed_no_conversion', 'won')),
  current_assignee_id uuid references public.profiles(user_id) on delete restrict,
  feedback_due_at timestamptz,
  parked_reason text check (parked_reason is null or parked_reason in ('no_eligible_seller', 'owner_blocked', 'campaign_pending')),
  source_phase text,
  estimated_value numeric(14,2) check (estimated_value is null or estimated_value >= 0),
  archived_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index leads_company_campaign_active_uq on public.leads(company_id, campaign_id) where archived_at is null;
create index leads_assignment_filter_idx on public.leads(assignment_status, source_entered_at, id) where archived_at is null;
create index leads_current_assignee_idx on public.leads(current_assignee_id, assignment_status) where archived_at is null;
create index leads_campaign_idx on public.leads(campaign_id, source_entered_at);

create table public.lead_source_records (
  id bigint generated always as identity primary key,
  source_lead_id text not null unique,
  import_run_id uuid not null references public.import_runs(id) on delete restrict,
  lead_id bigint references public.leads(id) on delete restrict,
  source_row integer not null check (source_row >= 2),
  source_entered_at timestamptz,
  campaign_external_id text,
  campaign_name text,
  mock_has_cnpj_or_mei text,
  full_name text,
  phone text,
  email extensions.citext,
  source_status text,
  row_hash text not null check (row_hash ~ '^[0-9a-f]{64}$'),
  normalized_payload jsonb not null,
  is_present boolean not null default true,
  removed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index lead_source_records_import_idx on public.lead_source_records(import_run_id);
create index lead_source_records_lead_idx on public.lead_source_records(lead_id);
create index lead_source_records_present_idx on public.lead_source_records(is_present, source_entered_at);

create table public.source_snapshot_records (
  import_run_id uuid not null references public.import_runs(id) on delete cascade,
  source_record_id bigint not null references public.lead_source_records(id) on delete cascade,
  observed_hash text not null check (observed_hash ~ '^[0-9a-f]{64}$'),
  outcome text not null check (outcome in ('created', 'updated', 'ignored', 'pending', 'error')),
  primary key (import_run_id, source_record_id)
);
create index source_snapshot_records_source_idx on public.source_snapshot_records(source_record_id);

create table public.source_data_issues (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state', 'campaign', 'contact_name', 'phone', 'email')),
  issue_code text not null,
  status text not null default 'open' check (status in ('open', 'resolved')),
  resolved_by uuid references public.profiles(user_id) on delete restrict,
  resolved_at timestamptz,
  created_at timestamptz not null default now()
);
create index source_data_issues_record_idx on public.source_data_issues(source_record_id);
create unique index source_data_issues_open_uq on public.source_data_issues(source_record_id, field_name) where status = 'open';

create table public.source_corrections (
  id bigint generated always as identity primary key,
  source_record_id bigint not null references public.lead_source_records(id) on delete restrict,
  field_name text not null check (field_name in ('document', 'state')),
  value text not null check (length(btrim(value)) > 0),
  normalized_value text not null,
  actor_id uuid not null references public.profiles(user_id) on delete restrict,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create index source_corrections_record_idx on public.source_corrections(source_record_id);
create unique index source_corrections_active_uq on public.source_corrections(source_record_id, field_name) where active;
