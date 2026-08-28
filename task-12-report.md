# Relatório da Tarefa 12 — Remoção Supabase e fechamento operacional

## Entrega

- Removidos `supabase/`, `tooling/supabase/`, o teste dependente desse tooling e o pacote `supabase` do workspace.
- Substituídos scripts Supabase por comandos PowerShell versionados para iniciar e encerrar o replica set MongoDB, aplicar bootstrap, iniciar API, web e worker.
- Criado `apps/api/.env.example` com somente `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET`. O exemplo web e a documentação operacional mantêm somente `NEXT_PUBLIC_API_URL` no cliente.
- Atualizados README, tarefa de inicialização, instruções de agente e evidências operacionais. Menções restantes a Supabase/PostgreSQL são registros históricos classificados no SPEC, roadmap, decisões ou relatórios de tarefas anteriores.
- Adicionado teste estrutural que exige os novos scripts e impede a volta dos diretórios e dependências removidos.
- O launcher local inicia API e web com `ProcessStartInfo` e ambiente isolado por processo; URI MongoDB e segredo de aplicação não aparecem nos argumentos de processos filhos. Os redirecionamentos conflitantes foram removidos.

## Verificação

```text
git diff --check
passed

node --test tooling/tests/workspace-structure.test.mjs
1 passed

PowerShell parser para os oito scripts operacionais
passed

node --test tooling/tests/local-stack-launcher.test.mjs
1 passed

scripts/start-local-stack.ps1 sem variáveis obrigatórias
falha controlada antes de iniciar Docker ou processos filhos

python -m pytest apps/api/tests -q
95 passed, 5 skipped

npm run lint
passed with 3 pre-existing warnings

npm run typecheck
passed

npm run test
6 files / 18 tests passed

npm run test:contracts
2 passed

npm run build
passed

npm run test:e2e
1 passed, 6 skipped
```

`npm run format:check` continua falhando por 24 arquivos pré-existentes fora desta tarefa. Os arquivos formatáveis modificados nesta tarefa foram verificados com Prettier individualmente.

## Limitações locais

Os cinco skips Python requerem MongoDB real em replica set. Os seis E2E de autenticação, papéis e ciclo de vida requerem API ativa, dados E2E e `API_CONTRACT_BASE_URL`; o CI configura esses pré-requisitos. O E2E de redirecionamento do visitante permanece executável localmente.
