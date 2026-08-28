# Relatório da Tarefa 6 — fila transacional MongoDB

## Entrega

- Regras puras de rodízio global, elegibilidade, perda de vez e consumo de créditos em `domain/queue.py`.
- `QueueService` com as quatro interfaces exigidas: distribuição normal, recorrência, atribuição temporária e transferência permanente.
- Repositório MongoDB com idempotência por comando e transação única para cursor versionado, crédito, assignment, lead, owner, auditoria e outbox.
- Primeiro assignment efetivo define `companies.ownerId`; recorrência e temporário preservam o owner e não movem o cursor.
- FIFO impede que um lead normal novo ultrapasse lead normal já parado.
- Índice único parcial protege um assignment atual por lead; índice único e validator protegem saldo único e não negativo por vendedor.
- Rotas internas autenticadas por chave para distribuição/recorrência e rotas administrativas autenticadas para temporário/transferência.

## Critérios cobertos

- AC-01 a AC-06: rotação, atraso, perda de vez, bloqueio por um atraso, estacionamento e FIFO.
- AC-07 a AC-08: recorrência sem movimento de cursor, crédito e consumo através de rotações.
- AC-09 a AC-11: owner bloqueado espera; temporário assume o lead, recebe crédito e o owner original permanece. O registro de venda será criado pela Tarefa 7, mas a fronteira exigida pelo AC-11 fica preservada por `assigneeId` temporário + `ownerId` original.
- Transferência permanente: altera somente owner futuro, preservando assignments históricos e auditando antes/depois.
- AC-29: teste concorrente em replica set valida assignments únicos, cursor equivalente ao sequencial e saldos não negativos.

## Evidências

Executado em `apps/api`:

```text
python -m pytest tests/unit/test_queue_rules.py tests/integration/test_queue_transactions.py tests/integration/test_queue_concurrency.py -q
15 passed, 1 skipped in 2.50s

python -m pytest -q
52 passed, 5 skipped in 9.93s
```

O skip adicional da Tarefa 6 é explícito: `test_queue_concurrency.py` requer um MongoDB real acessível como replica set. Os outros quatro skips preexistentes da suíte também dependem do MongoDB real. A cobertura transacional com adapter controlado roda sempre; a prova de conflito real fica ativa automaticamente quando `MONGODB_URI` aponta para um replica set.

Também executados com sucesso:

```text
python -m compileall -q src tests
git diff --check
```
