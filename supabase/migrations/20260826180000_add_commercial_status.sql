alter table public.leads
  add column if not exists commercial_status text not null default 'undefined'
  constraint leads_commercial_status_check
  check (commercial_status in ('undefined', 'negotiation', 'won', 'disqualified'));
