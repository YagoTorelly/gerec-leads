# Relatório da Tarefa 7 — calendário útil, SLA e operações

## Resultado

Foram implementados o calendário útil de São Paulo, o SLA inicial e periódico, feedbacks, notas administrativas, tentativas de WhatsApp e resultados comerciais transacionais no MongoDB.

As interfaces entregues são:

- `BusinessClock.add_business_hours(start, hours)`;
- `OperationsService.register_feedback(command)`;
- `OperationsService.register_attempt(command)`;
- `OperationsService.register_outcome(command)`.

## Regras cobertas

- AC-18: atribuição cria ciclo de 24 horas úteis e lembrete após 20 horas úteis; fins de semana e feriados nacionais/SP são ignorados integralmente.
- AC-19/AC-20: comentário exige 6 caracteres após `trim`; feedback exige contato explícito, fecha o ciclo anterior e abre o seguinte.
- AC-21: somente WhatsApp, uma tentativa por data útil, máximo de cinco datas distintas e desqualificação sempre por comando manual.
- AC-22: encerramento sem conversão mantém o lead qualificado e não o classifica como desqualificado.
- AC-23: Estado fora de SP não altera o lead automaticamente; a desqualificação exige decisão explícita.
- AC-24/AC-28: `won` fecha o SLA, cria evento/venda única, credita o responsável atual, marca a empresa cliente e preserva o proprietário.
- AC-30: nota administrativa é histórica, mas não fecha/renova ciclo nem altera o atraso do vendedor.

## Persistência e integração

Cada comando usa sessão e `with_transaction`, grava recibo idempotente em `command_results` e mantém lead, ciclo, histórico, auditoria, outbox, venda e empresa na mesma transação.

As mudanças adicionais ao conjunto mínimo de arquivos são necessárias para integrar as regras:

- `queue_repository.py`: cria o SLA inicial dentro da mesma transação da atribuição. Sem essa integração, um lead recém-atribuído não teria o prazo exigido pelo AC-18.
- `indexes.py`: protege uma tentativa por `leadId + businessDate` e um único ciclo aberto por lead, inclusive sob concorrência.
- `main.py`: injeta calendário, relógio, adapter transacional e registra as rotas.
- `test_queue_transactions.py`: comprova que a atribuição cria ciclo, lembrete e vencimento no mesmo commit.

## Evidência TDD e verificação

Os testes foram observados em RED antes da implementação: módulos ausentes, métodos `NotImplementedError`, rota 404 e índice inexistente. Depois, os ciclos GREEN focados foram executados.

Comando focado:

```text
python -m pytest tests/unit/test_business_time.py tests/unit/test_operations.py tests/integration/test_operations_transactions.py -q
33 passed in 4.58s (inclui regressões da fila e das operações)
```

Suíte completa da API:

```text
python -m pytest -q
77 passed, 5 skipped in 19.55s
```

Os cinco testes pulados já dependiam de um replica set MongoDB externo não configurado no ambiente local; a baseline anterior registrava os mesmos cinco skips.

`git diff --check` terminou sem erros; os avisos exibidos referem-se somente à conversão LF/CRLF configurada no worktree.

## Correção da revisão — rodada 1

- O outbox agora recebe `lead.feedback_due_soon` com `cycleId`, `scheduledFor`, `dueAt` e chave determinística `leadId:ciclo:feedback_due_soon`; o índice lógico e o recibo idempotente impedem duplicação no replay. Atribuições iniciais e renovações por feedback usam o mesmo evento agendável.
- `qualified_follow_up` e `qualified_closed_no_conversion` exigem `response_confirmed=True`, comprovando devolutiva real antes da qualificação. Resultados de desqualificação e ganho não exigem essa confirmação.
- `MongoOperationsRepository` aceita um `Clock` de sessão e obtém o instante dentro de `with_transaction`; o SLA e timestamps persistidos são recalculados com esse instante. A aplicação usa `MongoClock`, baseado no horário do servidor MongoDB, em vez de `SystemClock` de processo.
- `DuplicateKeyError` sem recibo idempotente é convertido em `OperationsStateError`, permitindo resposta HTTP 409 para colisões concorrentes.
