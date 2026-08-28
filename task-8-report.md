# Tarefa 8 — autorização, leituras e auditoria

## Entregas

- `PermissionService` exige usuário ativo/autenticado, restringe comandos administrativos a `admin` e gera filtros seller-scoped para leads, histórico, fila e saldo. O identificador vem exclusivamente de `CurrentUser`; não há parâmetro de `sellerId` nas leituras.
- `DashboardService.for_user` aplica o filtro antes de cada leitura e retorna páginas de leads, histórico, fila e saldo.
- Rotas autenticadas: `GET /api/dashboard`; administrativas: `GET /api/admin/users` e `GET /api/admin/audit`.
- Comandos críticos existentes de fila/operações continuam usando os serviços de domínio e gravando auditoria transacional com ator, ação, entidade, before/after, timestamp e correlation ID.
- Sessões antigas de usuários desativados já são rejeitadas por `AuthService.current_user`.

## Testes

```text
pytest -q
80 passed, 5 skipped in 17.15s
```

Os 5 skips dependem de MongoDB em replica set local.

## Commit

`feat(gerec-leads): aplica autorização e auditoria no backend`
