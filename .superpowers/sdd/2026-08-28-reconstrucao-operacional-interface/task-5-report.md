# Relatório da Task 5 — disponibilidade e rotação real da fila

## Status

Concluída no worktree `migracao-mongodb-vercel-railway`, sem rotas, UI, usuários, migração, deploy ou push.

## Entrega

- `SellerAvailability`, `QueueEntry` e `QueueSnapshot` materializam a projeção da fila no domínio.
- A disponibilidade é calculada por uma única função: pausa manual prevalece, ciclos SLA abertos vencidos bloqueiam e o restante fica ativo.
- O bloqueio consulta `feedback_cycles` abertos vencidos e o responsável atual; campos antigos do lead, inclusive prazo vencido em registro desqualificado, não bloqueiam sozinhos.
- A leitura circular inicia no cursor persistido e apresenta primeiro o próximo vendedor elegível, sem ocultar os demais.
- A distribuição persiste o próximo participante operacional elegível, pulando indisponibilidades sem restaurar turnos; o cursor e a atribuição continuam na mesma transação MongoDB.

## TDD e verificação

### RED

```text
python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q
```

Resultado observado: `4 failed, 19 passed, 1 skipped`. As falhas esperadas apontaram as interfaces ausentes de disponibilidade e snapshot.

### GREEN

```text
python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q
```

Resultado: `23 passed, 1 skipped`.

### Regressão abrangente

```text
python -m pytest apps/api/tests -q
git diff --check
```

Resultado: `132 passed, 8 skipped`; sem erros de whitespace. Os skips requerem MongoDB local em replica set, indisponível neste ambiente.

## Cobertura adicionada

- precedência da pausa sobre bloqueio automático;
- ciclo SLA aberto vencido, lead desqualificado sem ciclo aberto e regularização;
- preservação do lead na pausa;
- ordem circular iniciada no próximo elegível;
- cursor concorrente ao pular o primeiro vendedor bloqueado.

## Pendências preservadas

- `apps/api/.env.example` removido e `tools/google-sheets-diagnostic/` não rastreado: alterações preexistentes, alheias à Task 5.

## Correção — rodada 1/5

- O snapshot passou a usar a própria seleção normal em modo somente leitura. Assim, crédito de pulo também é considerado na primeira entrada apresentada: com Renato no cursor e um crédito, Sandra aparece e recebe a distribuição normal.
- Um ciclo aberto inconsistente ligado a lead com `isDisqualified` (ou status legado de desqualificação) não bloqueia o vendedor; somente ciclos pertencentes a SLA ainda ativo participam da derivação.
- Recorrência e atribuição temporária agora consultam o mesmo adaptador de disponibilidade da rotação, removendo as condições duplicadas de usuário, pausa e atraso.

### TDD da correção

```text
python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q
```

RED: `3 failed, 22 passed, 1 skipped`.

GREEN: `25 passed, 1 skipped`.

Verificação abrangente após a correção:

```text
python -m pytest apps/api/tests -q
git diff --check
```

Resultado: `134 passed, 8 skipped`; sem erros de whitespace.
