# Gerenciador de Leads WTG

O produto usa MongoDB como único banco, API e automações Python na Railway e cliente Next.js na Vercel. Leia `AGENTS.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md` antes de alterar o sistema.

## Pré-requisitos

- Node.js 24 LTS e npm para o cliente web.
- Python 3.12 ou 3.13 para API e workers.
- Docker Desktop para o replica set MongoDB local.

## Configuração local

Instale dependências uma vez:

```powershell
npm ci
cd apps/api
python -m pip install -e ".[dev]"
cd ../..
```

Defina variáveis somente no processo do backend ou worker. Use `apps/api/.env.example` como referência; os valores abaixo são placeholders locais, não credenciais reais:

```powershell
$env:MONGODB_URI = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
$env:MONGODB_DATABASE = "gerec_leads"
$env:APP_SECRET = "replace-with-a-local-secret"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
```

## Serviços locais

Em terminais separados, execute:

```powershell
npm run mongodb:start
npm run mongodb:bootstrap
npm run api:start
npm run web:start
npm run worker:start
```

`npm run start:local` inicia MongoDB, aplica o bootstrap e abre API e web em segundo plano. O worker continua um processo separado porque depende do webhook de entrega configurado para o ambiente. Para encerrar o banco, execute `npm run mongodb:stop`; acrescente `-RemoveVolumes` ao chamar `scripts/stop-mongodb.ps1` diretamente quando quiser apagar dados locais.

O cliente web recebe somente `NEXT_PUBLIC_API_URL`. `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` pertencem exclusivamente à API e aos workers Python; nunca os adicione ao ambiente Vercel ou a arquivos versionados.

## Verificação

```powershell
python -m pytest apps/api/tests -q
npm run lint
npm run typecheck
npm run test
npm run test:contracts
npm run build
npm run test:e2e
```

Consulte `infra/railway/README.md` para os comandos e variáveis de cada serviço Railway.
