# Gerenciador de Leads WTG

Projeto novo e isolado. Antes de desenvolver, leia `AGENTS.md`, o SPEC e o roadmap.

## Pré-requisitos

- Node.js 24 LTS
- npm
- Docker Desktop em execução

## Primeira execução

```powershell
nvm use 24
npm ci
npm run test:e2e:install
npm run supabase:start
npm run env:local
npm run supabase:bootstrap-users
npm run dev
```

Acesse `http://127.0.0.1:3000` e confirme “Supabase local conectado”.

## Verificação

```powershell
npm run typecheck
npm run test
npm run test:supabase-tooling
npm run build
```

## Encerramento

```powershell
npm run supabase:stop
```

`apps/web/.env.local` é gerado com URL pública, chave pública e a `SUPABASE_SERVICE_ROLE_KEY` apenas para uso server-side. O arquivo nunca deve ser versionado.

O bootstrap local reconcilia os cinco usuários, fixa a senha do admin em `Wtg@2026!Admin`, gera senhas aleatórias para os vendedores em `supabase/.temp/local-users.json` e popula campanhas, fila, histórico e leads demonstrativos no Supabase local.
