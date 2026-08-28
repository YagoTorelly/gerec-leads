# Relatório da Tarefa 6 — fila transacional MongoDB

## Entrega

- Regras puras de rodízio global, elegibilidade, perda de vez e consumo de créditos em `domain/queue.py`.
- `QueueService` com as quatro interfaces exigidas: distribuição normal, recorrência, atribuição temporária e transferência permanente.
- Repositório MongoDB com idempotência por comando e transação única para cursor versionado, crédito, assignment, lead, owner, auditoria e outbox.
- Primeiro assignment efetivo define `companies.ownerId`; recorrência e temporário preservam o owner e não movem o cursor.
- FIFO impede que um lead normal novo ultrapasse lead normal já parado.
- FIFO compara todos os leads normais elegíveis, tanto `ready` quanto `parked`, e usa espera limitada para permitir que uma transação concorrente mais antiga confirme primeiro.
- Índice único parcial protege um assignment atual por lead; índice único e validator protegem saldo único e não negativo por vendedor.
- Rotas internas autenticadas por chave para distribuição/recorrência e rotas administrativas autenticadas para temporário/transferência.
- Atribuição temporária aceita somente recorrência parada por `owner_unavailable`, exige owner prévio e nunca reivindica propriedade para um lead normal.
- Créditos criados e consumidos geram auditoria e outbox próprios com saldo anterior/posterior e `actorId`; rotas administrativas propagam o usuário autenticado e comandos internos registram o ator `system`.
- Transferência permanente pela API exige `confirmed: true` antes de executar o comando.

## Critérios cobertos

- AC-01 a AC-06: rotação, atraso, perda de vez, bloqueio por um atraso, estacionamento e FIFO.
- AC-06 inclui teste de dois leads `ready`, estacionamento por bloqueio total, regularização de Sandra e liberação FIFO sem restaurar vez perdida.
- AC-07 a AC-08: recorrência sem movimento de cursor, crédito e consumo através de rotações.
- AC-08 inclui três recorrências, três consumos em rotações distintas, saldo final zero e seis eventos auditáveis de crédito.
- AC-09 a AC-11: owner bloqueado espera; temporário assume o lead, recebe crédito e o owner original permanece. O registro de venda será criado pela Tarefa 7, mas a fronteira exigida pelo AC-11 fica preservada por `assigneeId` temporário + `ownerId` original.
- Transferência permanente: altera somente owner futuro, preservando assignments históricos e auditando antes/depois.
- AC-29: teste concorrente em replica set valida assignments únicos, cursor equivalente ao sequencial e saldos não negativos.

## Evidências

Executado em `apps/api`:

```text
python -m pytest tests/unit/test_queue_rules.py tests/integration/test_queue_transactions.py tests/integration/test_queue_concurrency.py -q
18 passed, 1 skipped

python -m pytest -q
55 passed, 5 skipped in 12.64s
```

O skip adicional da Tarefa 6 é explícito: `test_queue_concurrency.py` requer um MongoDB real acessível como replica set. Os outros quatro skips preexistentes da suíte também dependem do MongoDB real. A cobertura transacional com adapter controlado roda sempre; a prova de conflito real fica ativa automaticamente quando `MONGODB_URI` aponta para um replica set.

Também executados com sucesso:

```text
python -m compileall -q src tests
git diff --check
```
