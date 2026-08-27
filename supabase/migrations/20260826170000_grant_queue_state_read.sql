grant select on public.queue_state to authenticated;
create policy queue_state_authenticated_select
  on public.queue_state for select to authenticated using (true);
