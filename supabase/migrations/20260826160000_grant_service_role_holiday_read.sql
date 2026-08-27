-- O serviço de tentativas consulta feriados com a chave server-only.
-- O acesso é somente leitura; as regras de operação continuam no serviço.
grant select on public.business_holidays to service_role;
