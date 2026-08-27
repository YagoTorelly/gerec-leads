grant usage on schema private to authenticated, service_role;
grant execute on function private.current_user_role() to authenticated, service_role;
grant execute on function private.is_admin() to authenticated, service_role;
grant execute on function private.is_current_seller(uuid) to authenticated, service_role;
grant execute on function private.can_read_current_lead(bigint) to authenticated, service_role;
grant execute on function private.can_read_own_assignment(bigint) to authenticated, service_role;
