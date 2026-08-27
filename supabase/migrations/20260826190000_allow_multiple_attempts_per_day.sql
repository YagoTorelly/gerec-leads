-- O limite operacional é de cinco tentativas por ciclo, não de uma tentativa
-- por dia. A data continua sendo registrada para auditoria e ordenação.
alter table public.contact_attempts
  drop constraint if exists contact_attempts_lead_id_business_date_key;
