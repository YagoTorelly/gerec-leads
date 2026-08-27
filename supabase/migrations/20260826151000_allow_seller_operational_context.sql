create policy lead_source_records_current_seller_select
  on public.lead_source_records for select to authenticated
  using ((select private.can_read_current_lead(lead_id)));

create policy campaigns_current_seller_select
  on public.campaigns for select to authenticated
  using (exists (
    select 1 from public.leads l
    where l.campaign_id = campaigns.id
      and (select private.can_read_current_lead(l.id))
  ));
