# RelatÃ³rio da onda final de correÃ§Ã£o

Data: 2026-08-28
Base: `32bda27`

## Achados corrigidos

1. Respostas de dashboard e administraÃ§Ã£o agora serializam `ObjectId` recursivamente, inclusive em objetos e listas aninhados. HÃ¡ regressÃµes cobrindo payloads BSON reais na borda FastAPI.
2. `MongoClock` nÃ£o aceita sessÃ£o transacional. O instante do servidor Ã© capturado uma vez antes de `with_transaction` e reutilizado pelo callback e por eventuais retries, eliminando o comando `hello` proibido dentro da transaÃ§Ã£o.
3. `SyncJob` recebe `QueueService`, distribui cada lead cujo resultado de importaÃ§Ã£o esteja `ready` e usa uma chave idempotente estÃ¡vel por snapshot/lead. `QueueService.distribute_ready` escolhe recorrÃªncia ou fila global dentro do repositÃ³rio transacional.
4. ReimportaÃ§Ãµes alteram somente campos de origem. `assignmentStatus`, responsÃ¡vel, qualificaÃ§Ã£o, conversÃ£o, venda e evento final permanecem intactos; apenas a transiÃ§Ã£o legÃ­tima `pending_campaign -> ready` continua automÃ¡tica.
5. A fÃ¡brica de produÃ§Ã£o executa `ensure_schema` antes de construir/servir a API. O deploy Railway define `startCommand`, `/health` e timeout, portanto validators e Ã­ndices precisam estar aplicados antes de a instÃ¢ncia ficar saudÃ¡vel.

TambÃ©m foram corrigidos dois achados importantes diretamente relacionados ao ciclo operacional: motivos `outside_sp`/`no_cnpj` agora sÃ£o confrontados com os dados do lead/empresa, e um resultado terminal ou feedback renovado cancela o lembrete agendado do ciclo encerrado.

## Testes regressivos adicionados

- BSON aninhado em dashboard/admin e contrato 2xx;
- timestamp de servidor sem leitura dentro da transaÃ§Ã£o;
- distribuiÃ§Ã£o do sync exclusivamente via `QueueService`;
- preservaÃ§Ã£o de estado atribuÃ­do/final na reimportaÃ§Ã£o;
- bootstrap de schema antes da saÃºde Railway;
- compatibilidade de motivo de desqualificaÃ§Ã£o;
- cancelamento de lembrete quando o ciclo fecha.

## EvidÃªncias

- `python -m pytest apps/api/tests -q`: **102 passed, 5 skipped**. Os skips exigem replica set MongoDB externo.
- `npm run test`: **18 passed**.
- `npm run typecheck`: passou.
- `npm run lint`: passou sem erros; 3 warnings legados.
- `npm run build`: passou.
- `npm run test:contracts`: **2 passed**.
- testes de estrutura, launcher, tooling Playwright e contrato do CI: **4 passed**.
- `npm run test:e2e`: **1 passed, 6 skipped**; os seis fluxos autenticados exigem credenciais/dados E2E.
- `git diff --check`: passou.

## Escopo remanescente do reviewer

Este checkpoint conclui os cinco achados Critical e os dois itens operacionais acima. A restauraÃ§Ã£o ampla de telas/comandos administrativos, os novos jobs de notificaÃ§Ã£o, o endurecimento adicional do CI/AGENTS e os minors continuam pendentes para uma onda separada, conforme interrupÃ§Ã£o do coordenador antes do commit.
