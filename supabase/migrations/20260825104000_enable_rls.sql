create or replace function private.can_read_current_lead(target_lead_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.leads l
    where l.id = target_lead_id and l.current_assignee_id = (select auth.uid())
  );
$$;
create or replace function private.can_read_own_assignment(target_assignment_id bigint)
returns boolean language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.assignments a
    where a.id = target_assignment_id and a.seller_id = (select auth.uid())
  );
$$;
revoke all on function private.can_read_current_lead(bigint) from public, anon, authenticated, service_role;
revoke all on function private.can_read_own_assignment(bigint) from public, anon, authenticated, service_role;

alter table public.profiles enable row level security;
alter table public.seller_queue enable row level security;
alter table public.queue_state enable row level security;
alter table public.seller_skip_balances enable row level security;
alter table public.import_runs enable row level security;
alter table public.campaigns enable row level security;
alter table public.companies enable row level security;
alter table public.leads enable row level security;
alter table public.lead_source_records enable row level security;
alter table public.source_snapshot_records enable row level security;
alter table public.source_data_issues enable row level security;
alter table public.source_corrections enable row level security;
alter table public.assignments enable row level security;
alter table public.feedback_cycles enable row level security;
alter table public.feedbacks enable row level security;
alter table public.contact_attempts enable row level security;
alter table public.qualification_events enable row level security;
alter table public.sales enable row level security;
alter table public.business_holidays enable row level security;
alter table public.notification_outbox enable row level security;
alter table public.notification_incidents enable row level security;
alter table public.audit_log enable row level security;
alter table public.system_settings enable row level security;

alter table public.profiles force row level security;
alter table public.seller_queue force row level security;
alter table public.queue_state force row level security;
alter table public.seller_skip_balances force row level security;
alter table public.import_runs force row level security;
alter table public.campaigns force row level security;
alter table public.companies force row level security;
alter table public.leads force row level security;
alter table public.lead_source_records force row level security;
alter table public.source_snapshot_records force row level security;
alter table public.source_data_issues force row level security;
alter table public.source_corrections force row level security;
alter table public.assignments force row level security;
alter table public.feedback_cycles force row level security;
alter table public.feedbacks force row level security;
alter table public.contact_attempts force row level security;
alter table public.qualification_events force row level security;
alter table public.sales force row level security;
alter table public.business_holidays force row level security;
alter table public.notification_outbox force row level security;
alter table public.notification_incidents force row level security;
alter table public.audit_log force row level security;
alter table public.system_settings force row level security;

create policy profiles_select_self_or_admin on public.profiles for select to authenticated using (user_id = (select auth.uid()) or (select private.is_admin()));
create policy leads_admin_select on public.leads for select to authenticated using ((select private.is_admin()));
create policy leads_current_seller_select on public.leads for select to authenticated using ((select private.can_read_current_lead(id)));
create policy feedbacks_admin_select on public.feedbacks for select to authenticated using ((select private.is_admin()));
create policy feedbacks_current_or_historical_select on public.feedbacks for select to authenticated using (seller_id = (select auth.uid()) or (select private.can_read_current_lead(lead_id)));
create policy attempts_admin_select on public.contact_attempts for select to authenticated using ((select private.is_admin()));
create policy attempts_current_or_historical_select on public.contact_attempts for select to authenticated using (seller_id = (select auth.uid()) or (select private.can_read_current_lead(lead_id)));
create policy assignments_admin_select on public.assignments for select to authenticated using ((select private.is_admin()));
create policy assignments_own_select on public.assignments for select to authenticated using (seller_id = (select auth.uid()));
create policy feedback_cycles_admin_select on public.feedback_cycles for select to authenticated using ((select private.is_admin()));
create policy feedback_cycles_own_select on public.feedback_cycles for select to authenticated using ((select private.can_read_own_assignment(assignment_id)));
create policy qualification_events_admin_select on public.qualification_events for select to authenticated using ((select private.is_admin()));
create policy qualification_events_own_select on public.qualification_events for select to authenticated using (actor_id = (select auth.uid()) or (select private.can_read_current_lead(lead_id)));
create policy sales_admin_select on public.sales for select to authenticated using ((select private.is_admin()));
create policy sales_own_select on public.sales for select to authenticated using (credited_seller_id = (select auth.uid()));
create policy seller_queue_admin_select on public.seller_queue for select to authenticated using ((select private.is_admin()));
create policy seller_queue_own_select on public.seller_queue for select to authenticated using (seller_id = (select auth.uid()));
create policy skip_balances_admin_select on public.seller_skip_balances for select to authenticated using ((select private.is_admin()));
create policy skip_balances_own_select on public.seller_skip_balances for select to authenticated using (seller_id = (select auth.uid()));
create policy business_holidays_authenticated_select on public.business_holidays for select to authenticated using (true);
create policy campaigns_admin_select on public.campaigns for select to authenticated using ((select private.is_admin()));
create policy companies_admin_select on public.companies for select to authenticated using ((select private.is_admin()));
create policy companies_owner_select on public.companies for select to authenticated using (owner_id = (select auth.uid()));
create policy system_settings_admin_select on public.system_settings for select to authenticated using ((select private.is_admin()));

create policy profiles_service_role_write on public.profiles for all to service_role using (true) with check (true);
create policy seller_queue_service_role_write on public.seller_queue for all to service_role using (true) with check (true);
create policy queue_state_service_role_write on public.queue_state for all to service_role using (true) with check (true);
create policy skip_balances_service_role_write on public.seller_skip_balances for all to service_role using (true) with check (true);

create policy import_runs_admin_select on public.import_runs for select to authenticated using ((select private.is_admin()));
create policy source_snapshot_records_admin_select on public.source_snapshot_records for select to authenticated using ((select private.is_admin()));
create policy source_data_issues_admin_select on public.source_data_issues for select to authenticated using ((select private.is_admin()));
create policy source_corrections_admin_select on public.source_corrections for select to authenticated using ((select private.is_admin()));
create policy lead_source_records_admin_select on public.lead_source_records for select to authenticated using ((select private.is_admin()));
create policy notification_outbox_admin_select on public.notification_outbox for select to authenticated using ((select private.is_admin()));
create policy notification_incidents_admin_select on public.notification_incidents for select to authenticated using ((select private.is_admin()));
create policy audit_admin_select on public.audit_log for select to authenticated using ((select private.is_admin()));

revoke all on all tables in schema public from anon, authenticated;
grant all on public.profiles, public.seller_queue, public.queue_state, public.seller_skip_balances to service_role;
grant select on public.profiles, public.seller_queue, public.seller_skip_balances, public.leads,
  public.feedbacks, public.contact_attempts, public.assignments, public.feedback_cycles,
  public.qualification_events, public.sales, public.business_holidays, public.campaigns,
  public.companies, public.system_settings to authenticated;
