begin;
select plan(30);

select ok(to_regclass('public.profiles') is not null, 'profiles');
select ok(to_regclass('public.seller_queue') is not null, 'seller_queue');
select ok(to_regclass('public.queue_state') is not null, 'queue_state');
select ok(to_regclass('public.seller_skip_balances') is not null, 'seller_skip_balances');
select ok(exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'profiles' and column_name = 'user_id'), 'user_id');
select ok(exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'profiles' and column_name = 'role'), 'role');
select ok(exists (select 1 from information_schema.columns where table_schema = 'public' and table_name = 'profiles' and column_name = 'role' and data_type = 'text'), 'role is text');
select ok(exists (select 1 from pg_constraint where conname = 'profiles_role_check'), 'profiles_role_check');
select ok(exists (select 1 from pg_index i join pg_class c on c.oid = i.indexrelid join pg_attribute a on a.attrelid = i.indrelid and a.attnum = any(i.indkey) where i.indrelid = 'public.profiles'::regclass and c.relname like '%pkey' and a.attname = 'user_id'), 'user_id is primary key');
select ok(to_regclass('public.seller_queue_position_idx') is not null, 'seller_queue_position_idx');
select ok(
  exists (
    select 1
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'private'
      and p.proname = 'is_admin'
      and p.pronargs = 0
  ),
  'private.is_admin exists'
);
select ok(to_regclass('public.import_runs') is not null, 'import_runs');
select ok(to_regclass('public.lead_source_records') is not null, 'lead_source_records');
select ok(to_regclass('public.source_data_issues') is not null, 'source_data_issues');
select ok(to_regclass('public.source_corrections') is not null, 'source_corrections');
select ok(to_regclass('public.campaigns') is not null, 'campaigns');
select ok(to_regclass('public.companies') is not null, 'companies');
select ok(to_regclass('public.leads') is not null, 'leads');
select ok(to_regclass('public.source_snapshot_records') is not null, 'source_snapshot_records');
select ok(exists (select 1 from pg_constraint where conrelid = 'public.lead_source_records'::regclass and contype = 'u' and pg_get_constraintdef(oid) like '%source_lead_id%'), 'source_lead_id unique');
select ok(to_regclass('public.assignments') is not null, 'assignments');
select ok(to_regclass('public.feedback_cycles') is not null, 'feedback_cycles');
select ok(to_regclass('public.feedbacks') is not null, 'feedbacks');
select ok(to_regclass('public.contact_attempts') is not null, 'contact_attempts');
select ok(to_regclass('public.qualification_events') is not null, 'qualification_events');
select ok(to_regclass('public.sales') is not null, 'sales');
select ok(to_regclass('public.business_holidays') is not null, 'business_holidays');
select ok(to_regclass('public.notification_outbox') is not null, 'notification_outbox');
select ok(to_regclass('public.audit_log') is not null, 'audit_log');
select ok(to_regclass('public.system_settings') is not null, 'system_settings');

select * from finish();
rollback;
