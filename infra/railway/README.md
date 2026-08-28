# Serviços Railway

`railway.json` contém apenas o build compartilhado. Como cada serviço Railway possui seu próprio comando de início, configure os três processos abaixo no painel do ambiente correspondente.

| Serviço | Tipo | Comando | Agenda |
| --- | --- | --- | --- |
| `api` | persistente/web | `uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}` via `apps/api/Dockerfile` | — |
| `outbox-worker` | persistente/worker | `python -m gerec_api.automation.outbox_worker` | — |
| `google-sheets-sync` | cron | `python -m gerec_api.automation.scheduler` | `*/5 * * * *` |

Defina `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` em cada serviço no painel Railway. Para o cron, defina `GOOGLE_SHEETS_SPREADSHEET_ID`, `GOOGLE_SHEETS_RANGE` e `GOOGLE_SERVICE_ACCOUNT_JSON`; para o worker, `OUTBOX_DELIVERY_WEBHOOK_URL` e, se necessário, `OUTBOX_DELIVERY_TOKEN`. Todos os valores ficam exclusivamente nas variáveis Railway; não registre valores no repositório. O cron deve finalizar após cada execução e retornar erro quando a sincronização falhar.

Os jobs usam a mesma camada de domínio da API. O sincronizador só finaliza o snapshot após importar todas as linhas e mantém lease com geração/token; uma geração antiga não arquiva um snapshot novo. O worker reivindica cada evento com claim token, aplica fencing no ack/retry e encaminha a chave de idempotência ao provedor.
