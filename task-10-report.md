# Relatório da Tarefa 10 — Automações Python Railway

## Entrega

- Criados `sync_job.py`, `outbox_worker.py` e `scheduler.py` no pacote Python da API.
- `run_sync(source, run_id)` usa somente `LeadService`: processa o snapshot completo, fixa `source_snapshot_id` no `run_id`, usa uma chave estável por linha e só chama o arquivamento depois de todas as importações concluírem.
- `process_outbox(batch_size)` é composto sobre uma outbox Mongo com claim atômico, lease, tentativas limitadas, retry e dead-letter. Cada evento leva sua chave de idempotência ao adaptador de entrega; `notification_incidents` recebe no máximo um incidente por evento terminal.
- `run_due_jobs(now)` serializa o sync pelo slot UTC de cinco minutos em `automation_job_locks`; falhas liberam o lock sem marcar o slot como concluído.
- Índices únicos protegem `notification_outbox.idempotencyKey` e `notification_incidents.outboxEventId`. A coleção de locks entrou no bootstrap Mongo. Essa extensão de `test_indexes.py` registra precisamente esses novos invariantes, sem alterar regra existente.
- Eventos de operações agora sempre iniciam `attempts: 0`; lembretes com `status: scheduled` tornam-se elegíveis somente em `scheduledFor`.
- Adicionados `railway.json` e `infra/railway/README.md` com os processos `api`, `outbox-worker` e cron de sync `*/5 * * * *`, além das variáveis server-side obrigatórias `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET`.
- `integrations/n8n/README.md` agora registra a remoção da integração: o novo sistema não usa n8n.

## Cobertura

- Replay de snapshot completo com chaves de linha estáveis.
- Retry do worker e entrega única após sucesso.
- Exclusão mútua do scheduler no mesmo slot e execução no slot seguinte.
- Contrato de deploy Railway sem credenciais versionadas.
- Eventos de feedback com contador de tentativas inicial.

## Verificação

```text
pytest -q
89 passed, 5 skipped in 15.35s

python -m compileall -q src
passed

python -m json.tool railway.json
passed
```

Os cinco skips continuam exigindo MongoDB local em replica set.

## Limite externo explícito

O provedor de e-mail definitivo ainda não foi escolhido. `OutboxWorker` aceita o adaptador de entrega que deverá ser composto no ambiente Railway, preservando a chave de idempotência; o worker não finge que uma mensagem foi entregue sem um adaptador configurado.
