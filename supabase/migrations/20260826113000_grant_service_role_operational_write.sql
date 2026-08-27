grant all on public.import_runs, public.campaigns, public.companies, public.leads,
  public.lead_source_records, public.assignments, public.feedback_cycles,
  public.feedbacks, public.contact_attempts, public.qualification_events,
  public.sales, public.audit_log to service_role;

grant usage, select on all sequences in schema public to service_role;
