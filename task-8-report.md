# Tarefa 8 — autorização, leituras e auditoria

## Entregas

- `PermissionService` exige usuário ativo/autenticado, restringe comandos administrativos a `admin` e gera filtros seller-scoped para leads, histórico, fila e saldo. O identificador vem exclusivamente de `CurrentUser`; não há parâmetro de `sellerId` nas leituras.
- `DashboardService.for_user` aplica o filtro antes de cada leitura e retorna páginas de leads, histórico, fila e saldo.
- Rotas autenticadas: `GET /api/dashboard`; administrativas: `GET /api/admin/users` e `GET /api/admin/audit`.
- Comandos críticos existentes de fila/operações continuam usando os serviços de domínio e gravando auditoria transacional com ator, ação, entidade, before/after, timestamp e correlation ID.
- Sessões antigas de usuários desativados já são rejeitadas por `AuthService.current_user`.

## Correções do round 1

- Leads de seller usam apenas `assigneeId`; histórico permanece em consulta própria.
- Dashboard e administração aceitam `page`/`limit`, calculam `skip` e validam limites.
- Toda leitura administrativa recebe `CurrentUser` e filtro explícito; filtro ausente é rejeitado.
- Auditoria operacional captura snapshots `before`/`after` de lead, ciclo e empresa dentro da transação.
- Fakes e testes cobrem paginação página 2 e isolamento seller A/B.
- Notas administrativas também registram snapshots reais do lead/ciclo (sem mutar SLA), e chamadas diretas do dashboard rejeitam `limit=0`.
- Rotas administrativas têm teste HTTP de `403` para seller; testes cobrem snapshots de tentativa, outcome, nota administrativa, histórico, fila e saldo.

## Testes

```text
pytest -q
85 passed, 5 skipped in 17.03s
```

Os 5 skips dependem de MongoDB em replica set local.

## Commit

Commit inicial: `743c068 feat(gerec-leads): aplica autorização e auditoria no backend`

Commit de correção: `fix(gerec-leads): fecha escopos, paginação e snapshots de auditoria`

Commit round 2: `fix(gerec-leads): completa auditoria e valida paginação`
