# Task 1 — Relatório de implementação

## Status

Implementada a criação transacional de leads manuais com fila/cursor próprios,
ID `MAN-` + UUID4, situação inicial `undefined`, herança restrita de
campanha/origem, salto de vendedores pausados e recibo idempotente.

## Arquivos

- Criado `apps/api/src/gerec_api/domain/manual_leads.py`.
- Alterado `apps/api/src/gerec_api/domain/queue.py`.
- Alterado `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`.
- Alterado `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`.
- Criado `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260922_manual_queue_exportations.py`.
- Alterado `apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py` para registrar a migração.
- Alterado `apps/api/src/gerec_api/infrastructure/mongo/indexes.py` para declarar o índice único parcial de `manualQueueLeadId`.
- Alterado `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py` para validar o UUID manual e permitir campanha vazia somente no contrato de origem manual.
- Criado `apps/api/tests/integration/test_manual_leads.py`.

## Evidência TDD

- RED inicial: `python -m pytest apps/api/tests/integration/test_manual_leads.py -q`
  falhou na coleta com `ModuleNotFoundError: gerec_api.domain.manual_leads`.
- RED de schema: a mesma suíte apresentou 2 falhas pela migração e pelo índice
  ainda ausentes.
- RED de integração com o modelo automático real: o teste de herança falhou
  com `origin=None` ao usar `adName` como origem persistida.
- GREEN focado: 8 testes aprovados.

## Comandos e contagens

- `python -m pytest apps/api/tests/integration/test_manual_leads.py -q` — 8 passed.
- `python -m pytest apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py apps/api/tests/integration/test_indexes.py apps/api/tests/integration/test_operational_migration.py -q` — 33 passed, 8 skipped.
- `python -m compileall -q apps/api/src apps/api/tests` — exit 0.
- `python -m pytest apps/api/tests -q` — 195 passed, 9 skipped.
- `git diff --check` — exit 0.

## Riscos e limites

- O Docker Desktop/replica set local não estava disponível; por isso 9 testes
  que dependem de MongoDB real foram pulados. Os testes transacionais com o
  adapter em memória e toda a suíte restante passaram, mas concorrência e
  aplicação física do novo índice ainda dependem do gate com replica set.
- A rota/autorização HTTP e a integração final da janela de notificações são
  escopo da Task 2; esta task já grava `lead.assigned` na outbox.
- `apps/api/.env.example` removido e `tools/google-sheets-diagnostic/` não
  rastreado já estavam no worktree e foram preservados sem alteração/stage.

## Correção pós-revisão — rodada 1

### Findings corrigidos

- O reconciliador e o FIFO automáticos agora excluem `source="manual"`. Foi
  criado um reconciliador manual explícito que preserva a ordem própria e usa
  somente o cursor `_id="manual"`; o ciclo estacionado/reativado não lê nem
  altera cursor ou créditos automáticos.
- O seletor público automático persiste cada crédito de pulo consumido na mesma
  transação do avanço do cursor e registra auditoria/outbox
  `seller.skip_consumed`.
- A auditoria `lead.manual_created` preserva o payload recebido, anterior à
  normalização usada para persistência.
- Foram adicionados testes de MongoDB real para concorrência/idempotência,
  unicidade física de `manualQueueLeadId`, rollback integral do comando manual
  e rollback conjunto de cursor/crédito. A fixture só pula quando a conexão ou
  o replica set requerido estão realmente indisponíveis; falhas de schema e de
  execução continuam sendo falhas de teste.

### Evidência RED → GREEN

- RED de isolamento: o reconciliador genérico atribuiu o lead manual estacionado
  como `normal` e avançou o cursor automático; GREEN após particionar consulta,
  FIFO e comando de reconciliação manual.
- RED de crédito: o seletor automático retornou o próximo vendedor, mas manteve
  o saldo em `1`; GREEN após débito e auditoria transacionais.
- RED de auditoria: o log continha e-mail/campos normalizados; GREEN após separar
  payload original dos valores normalizados.
- Os testes reais de concorrência e rollback foram coletados, mas não executados
  neste ambiente porque não há membro disponível para o replica set `rs0`.

### Arquivos alterados na correção

- `apps/api/src/gerec_api/domain/manual_leads.py`
- `apps/api/src/gerec_api/domain/queue.py`
- `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`
- `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`
- `apps/api/tests/integration/test_manual_leads.py`
- `.superpowers/sdd/2026-09-22-cadastro-manual-fila-alternativa-exportacoes/task-1-report.md`

### Verificação da correção

- `python -m pytest apps/api/tests/integration/test_manual_leads.py -q -rs`
  — 11 passed, 3 skipped (replica set `rs0` indisponível).
- `python -m pytest apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py apps/api/tests/integration/test_manual_leads.py -q -rs`
  — 31 passed, 4 skipped (replica set `rs0` indisponível).
- `python -m pytest apps/api/tests -q -rs`
  — 198 passed, 12 skipped (todos os skips reportados por infraestrutura MongoDB
  replica set indisponível).
- `python -m compileall -q apps/api/src apps/api/tests` — exit 0.
- `git diff --check` — exit 0.

### Risco residual

- Os três novos cenários transacionais reais permanecem pendentes de execução
  em uma infraestrutura MongoDB replica set disponível; não houve fallback para
  fake nesses testes. Todo o restante da suíte da API passou.
