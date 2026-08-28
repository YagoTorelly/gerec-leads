# Relatório da Tarefa 10 — Automações Python Railway

## Entrega

- Criados `sync_job.py`, `outbox_worker.py` e `scheduler.py` no pacote Python da API.
- `run_sync(source, run_id)` usa somente `LeadService`: processa o snapshot completo, fixa `source_snapshot_id` no `run_id`, usa uma chave estável por linha e só chama o arquivamento depois de todas as importações concluírem.
- `process_outbox(batch_size)` é composto sobre uma outbox Mongo com claim atômico, claim token/fencing, tentativas limitadas, retry e dead-letter. Cada evento leva sua chave de idempotência ao webhook configurado na Railway; `notification_incidents` recebe no máximo um incidente por evento terminal. Sem URL do provedor, o worker falha antes de reivindicar eventos.
- `run_due_jobs(now)` serializa o sync pelo slot UTC de cinco minutos em `automation_job_locks`; falhas liberam o lock sem marcar o slot como concluído e o entrypoint retorna código não zero.
- `GoogleSheetsAdapter` consulta a API Values do Google Sheets com `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_RANGE` e `GOOGLE_SHEETS_ACCESS_TOKEN` exclusivamente no ambiente Railway, mantendo a validação exata do contrato A–Q.
- O sync usa lease com token e geração, renovado antes de cada linha e antes do arquivamento. Ao perder a geração, aborta sem chamar `archive_missing`.
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
- Fencing de outbox contra worker com lease vencido; provider recebe `Idempotency-Key`; sync antigo não arquiva snapshot novo; cron falho retorna exit code 1.
- Payloads reais da outbox com `ObjectId` e `datetime` são projetados para strings JSON antes do POST, sem alterar sua chave de idempotência.

## Verificação

```text
pytest -q
95 passed, 5 skipped in 15.83s

python -m compileall -q src
passed

python -m json.tool railway.json
passed
```

Os cinco skips continuam exigindo MongoDB local em replica set.

## Composição externa

O worker usa um webhook configurado no ambiente Railway e encaminha `Idempotency-Key`; o provedor final deve respeitar essa chave. Não há credenciais no repositório.
