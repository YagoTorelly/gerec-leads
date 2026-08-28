# Relatório da Tarefa 11 — Deploy Vercel, contratos e E2E

## Entrega

- Criado `vercel.json` para o deploy do workspace Next.js sem segredos versionados. A única variável necessária na Vercel permanece `NEXT_PUBLIC_API_URL`.
- A API Railway agora envia `X-Gerec-API-Contract-Version: 1` em todas as respostas. Os contratos iniciam um processo FastAPI controlado, com banco em memória, e verificam health, login, sessão, erros e payloads mínimos de auth, imports/leads, queue, operations e admin.
- A resposta administrativa agora remove `passwordHash` e `tokenHash`. A alteração em `admin.py` foi necessária porque o contrato controlado expôs que `GET /api/admin/users` retornava o hash de senha, contrariando a exigência de não expor segredos.
- A suíte Playwright cobre o visitante sem sessão, login, usuário desativado, navegação de administrador, isolamento do vendedor, interação de tentativa pela interface, ciclo contato → qualificado → ganho idempotente, nova venda com chave distinta rejeitada e cinco tentativas antes da desqualificação manual.
- O workflow GitHub Actions inicia MongoDB em replica set, API Python e Next.js, cria dados isolados de E2E, executa Python, verificações web escopadas, contratos e E2E; o encerramento de processos e volumes ocorre com `if: always()`. Somente `npm run format:check` é informativo com `continue-on-error`; lint, typecheck, Vitest, contratos e E2E permanecem bloqueantes.
- `APP_SECRET` e a senha E2E são gerados pelo runner com `openssl` e persistidos apenas no ambiente efêmero do job. O servidor de contratos recebe segredo e senha aleatórios do processo Node, sem valores de credencial literais no repositório.

## Verificação

```text
python -m pytest apps/api/tests -q
95 passed, 5 skipped

npm run typecheck
passed

npm run lint
passed

npm run test
6 files / 18 tests passed

npm run test:e2e
1 passed, 6 skipped sem API, credenciais e fixture E2E locais

node --test tests/contracts/api-contracts.test.mjs
2 passed

node --test tooling/tests/ci-contract.test.mjs
1 passed
```

`npm run check` continua bloqueado por formatação pré-existente: o Prettier lista 42 arquivos fora do escopo desta tarefa, inclusive arquivos não modificados. Todos os arquivos TypeScript/JSON/YAML alterados nesta tarefa foram verificados individualmente com Prettier.

## Limitações locais

Os cinco skips Python exigem MongoDB local em replica set. Os seis E2E de autenticação, papéis e ciclo exigem API ativa, usuários/dados E2E e `API_CONTRACT_BASE_URL`; o CI fornece esses pré-requisitos. O teste de fundação continua executável localmente sem a API.
