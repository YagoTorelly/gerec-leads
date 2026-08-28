# Evidência operacional da migração MongoDB, Vercel e Railway

## Arquitetura operacional

- MongoDB é a única persistência, no database `gerec_leads`, com replica set obrigatório.
- API e worker Python recebem `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` somente no ambiente do processo ou no painel Railway.
- A Vercel recebe somente `NEXT_PUBLIC_API_URL`; MongoDB e segredos nunca são enviados ao cliente web.
- Os artefatos Supabase e seu tooling foram removidos após cobertura equivalente por API, contratos e E2E.

## Reprodução local

```powershell
npm ci
cd apps/api
python -m pip install -e ".[dev]"
cd ../..
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
$env:MONGODB_DATABASE = "gerec_leads"
$env:APP_SECRET = "replace-with-a-local-secret"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run mongodb:start
npm run mongodb:bootstrap
npm run api:start
npm run web:start
npm run worker:start
```

Os comandos Railway e as variáveis adicionais para Google Sheets e entrega de notificações estão em `infra/railway/README.md`.

## Verificação

Os resultados da verificação final e as limitações locais estão registrados em `task-12-report.md`.
