# Task 4 — Comando transacional de tratativa

## Status

Concluída no worktree `migracao-mongodb-vercel-railway`, sem rota HTTP, UI, usuários, fila, migração, deploy ou push.

## Entrega

- `TreatmentCommand` e `TreatmentResult` com situação primária fechada: `undefined`, `negotiation` ou `won`.
- Somente o vendedor atualmente responsável pode registrar a tratativa.
- Cada submissão cria documento imutável em `lead_treatments`, atualiza a projeção do lead, grava auditoria, outbox e recibo de idempotência na mesma transação.
- `isDisqualified` preserva a situação `won`, fecha o SLA e impede que tratativas posteriores o reabram automaticamente.
- A tratativa não deixa status legados exclusivos impedirem a projeção comercial aprovada.

## TDD

### RED

Comando executado antes da implementação:

```text
python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q
```

Resultado: falha de coleta esperada, pois `TreatmentCommand` e `TreatmentResult` ainda não existiam em `gerec_api.domain.operations`.

### GREEN

Comando específico após a implementação:

```text
python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q
```

Resultado final: `22 passed`.

Verificação abrangente:

```text
python -m pytest apps/api/tests -q
git diff --check
```

Resultado: `127 passed, 8 skipped`; `git diff --check` sem erros.

## Cobertura nova

- comentário de cinco caracteres, situação ausente e desqualificação sem comentário;
- negação para administrador e vendedor que não é o responsável atual;
- projeção, evento imutável, auditoria e renovação de SLA;
- `won + isDisqualified`, preservação do marcador e não reabertura do SLA;
- idempotência sem incremento duplicado;
- rollback de evento, lead, auditoria, ciclo e recibo;
- compatibilidade da projeção com estados legados exclusivos.

## Pendências preservadas

- `apps/api/.env.example` removido, alteração preexistente e alheia à Task 4.
- `tools/google-sheets-diagnostic/` não rastreado, preexistente e alheio à Task 4.
