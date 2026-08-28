# Serviços Railway

`railway.json` contém apenas o build compartilhado. Como cada serviço Railway possui seu próprio comando de início, configure os três processos abaixo no painel do ambiente correspondente.

| Serviço | Tipo | Comando | Agenda |
| --- | --- | --- | --- |
| `api` | persistente/web | `uvicorn gerec_api.main:create_app --factory --host 0.0.0.0 --port $PORT` | — |
| `outbox-worker` | persistente/worker | `python -m gerec_api.automation.outbox_worker` | — |
| `google-sheets-sync` | cron | `python -m gerec_api.automation.scheduler` | `*/5 * * * *` |

Defina `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` em cada serviço no painel Railway. Defina também a fonte e as credenciais de integrações externas exclusivamente nas variáveis Railway; não registre valores no repositório. O cron deve finalizar após cada execução.

Os jobs usam a mesma camada de domínio da API. O sincronizador só finaliza o snapshot após importar todas as linhas; o worker reivindica cada evento com lock MongoDB e reutiliza sua chave de idempotência nas tentativas.
