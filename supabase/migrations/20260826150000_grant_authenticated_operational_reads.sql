-- As políticas RLS definem quais linhas cada perfil pode ver; o privilégio
-- de tabela também precisa existir para que o PostgREST consiga avaliá-las.
grant select on public.lead_source_records,
  public.import_runs,
  public.source_snapshot_records,
  public.source_data_issues,
  public.source_corrections,
  public.audit_log to authenticated;
