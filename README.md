# Gerenciador de Leads WTG

Projeto novo e isolado. Antes de desenvolver, leia `AGENTS.md`, o SPEC e o roadmap.

## Pré-requisitos

- Node.js 24 LTS e npm (cliente web)
- Python 3.12 ou 3.13 (API)
- Docker Desktop em execução (MongoDB local)

## MongoDB local

O MongoDB local roda como replica set `rs0`, requisito para as transações do produto:

```powershell
docker compose -f infra/mongodb/docker-compose.yml up -d
```

Para encerrar:

```powershell
docker compose -f infra/mongodb/docker-compose.yml down
```

## API Python

Instale as dependências de desenvolvimento e defina os valores apenas no ambiente do processo da API. Os exemplos abaixo são placeholders, não credenciais reais:

```powershell
cd apps/api
python -m pip install -e ".[dev]"
$env:MONGODB_URI = "mongodb://localhost:27017/?replicaSet=rs0"
$env:MONGODB_DATABASE = "gerec_leads"
$env:APP_SECRET = "replace-with-a-local-secret"
python -m uvicorn gerec_api.main:create_app --factory --reload
```

Verifique a fundação da API:

```powershell
cd apps/api
python -m pytest -q
```

As credenciais MongoDB e os segredos de aplicação pertencem exclusivamente aos processos Python do backend e dos jobs na Railway; eles nunca devem ser enviados ao cliente web na Vercel.
