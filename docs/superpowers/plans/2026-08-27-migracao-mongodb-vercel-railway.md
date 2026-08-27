# Migração MongoDB, Vercel e Railway — Plano de Implementação

> **Para agentes:** REQUISITO: usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa por tarefa. Os passos usam caixas de seleção (`- [ ]`).

**Objetivo:** substituir integralmente Supabase/PostgreSQL por um backend Python transacional na Railway, MongoDB como banco único e site Next.js publicado na Vercel.

**Arquitetura:** O navegador acessa somente o site Next.js na Vercel. O site chama uma API Python na Railway. API e workers Python compartilham o database MongoDB `gerec_leads`; apenas o backend possui a URI e credenciais. Regras de fila, SLA, propriedade, resultados e auditoria vivem nos módulos de domínio Python e são confirmadas em transações MongoDB.

**Stack:** Python 3.12+, FastAPI, PyMongo, Pydantic Settings, Argon2id, pytest, MongoDB replica set, Next.js 16, React 19, TypeScript e Playwright.

**Spec:** `docs/superpowers/specs/2026-08-27-migracao-mongodb-design.md` e `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, após atualização canônica prevista na Tarefa 1.

## Restrições globais

- O MongoDB é o único banco e usa o database `gerec_leads`.
- A Vercel hospeda somente o site Next.js e assets públicos.
- A Railway hospeda a API Python e automações Python.
- O navegador nunca recebe URI, usuário ou senha do MongoDB.
- O MongoDB local, staging e produção operam com replica set para transações.
- O SPEC continua sendo a fonte de verdade das regras de negócio.
- A interface continua exclusivamente desktop, com largura mínima suportada de 1280 px.
- Senhas são derivadas com Argon2id ou scrypt; nunca são armazenadas em texto puro.
- Todo comando crítico possui idempotência, auditoria e teste de rollback/concorrência.
- Dados do workbook mock permanecem sintéticos; a coluna `você_tem_cnpj_ou_mei?` não é CNPJ.
- Nenhuma migração de dados comerciais será feita, pois o MongoDB está vazio.

## Arquivos e módulos

| Área | Arquivos principais | Responsabilidade |
|---|---|---|
| Backend Python | `apps/api/pyproject.toml`, `apps/api/src/gerec_api/` | API, autenticação, domínio e acesso ao MongoDB |
| Domínio | `apps/api/src/gerec_api/domain/` | Fila, SLA, leads, resultados e invariantes |
| Persistência | `apps/api/src/gerec_api/infrastructure/mongo/` | Cliente, transações, coleções e índices |
| Automação | `apps/api/src/gerec_api/automation/` | Sync do workbook, outbox, e-mails e jobs Railway |
| Site | `apps/web/src/` | Telas e cliente HTTP da API Python |
| Infra local | `infra/mongodb/`, `scripts/` | Replica set, variáveis e comandos locais |
| Contratos | `tests/contracts/`, `apps/api/tests/`, `tests/e2e/` | Contratos, integração, concorrência e E2E |

---

### Tarefa 1: Registrar a mudança canônica de arquitetura

**Arquivos:**
- Modificar: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` nas seções 6, 7, 25, 26, 28, 36, 37, 38 e 39
- Modificar: `docs/ARQUITETURA.md`
- Modificar: `docs/DECISOES.md`
- Modificar: `ROADMAP.md`
- Teste: `tooling/tests/workspace-structure.test.mjs`

**Interfaces produzidas:** documentação canônica alinhada ao desenho MongoDB/Vercel/Railway; nenhuma regra funcional é removida.

- [ ] **Passo 1: Escrever asserções de governança**

Adicionar ao teste verificações de que a arquitetura menciona MongoDB, Vercel e Railway, que Supabase não aparece como dependência futura e que o database é `gerec_leads`.

- [ ] **Passo 2: Rodar o teste e confirmar a falha**

Executar: `node --test tooling/tests/workspace-structure.test.mjs`

Resultado esperado: falha até a documentação registrar a nova arquitetura.

- [ ] **Passo 3: Atualizar documentação**

Registrar a regra anterior, a nova regra, motivo, impacto nulo nos dados, impacto nas métricas, migração necessária, testes e aprovação de Yago. Atualizar o roadmap para separar fundação MongoDB, backend Python, site Vercel e automações Railway.

- [ ] **Passo 4: Validar documentação**

Executar: `git diff --check` e `node --test tooling/tests/workspace-structure.test.mjs`

- [ ] **Passo 5: Commitar**

```bash
git add SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/ARQUITETURA.md docs/DECISOES.md ROADMAP.md tooling/tests/workspace-structure.test.mjs
git commit -m "docs(gerec-leads): oficializa MongoDB Vercel e Railway"
```

### Tarefa 2: Criar o backend Python e o MongoDB local

**Arquivos:**
- Criar: `apps/api/pyproject.toml`
- Criar: `apps/api/src/gerec_api/main.py`
- Criar: `apps/api/src/gerec_api/config.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/client.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/collections.py`
- Criar: `infra/mongodb/docker-compose.yml`
- Criar: `apps/api/tests/test_health.py`
- Modificar: `README.md`, `.gitignore`

**Interfaces:**
- `Settings.from_env() -> Settings`
- `MongoClientFactory.create(settings) -> MongoDatabase`
- `create_app() -> FastAPI`
- `GET /health` retorna `{ "status": "ok", "database": "gerec_leads" }`

- [ ] **Passo 1: Escrever teste vermelho da API e configuração**

Testar que `create_app()` expõe `/health` e que configuração ausente gera erro sem tentar conexão implícita.

- [ ] **Passo 2: Configurar dependências Python**

Usar `pyproject.toml` com FastAPI, Uvicorn, PyMongo, Pydantic Settings, Argon2 e pytest. Fixar Python `>=3.12,<3.14`.

- [ ] **Passo 3: Configurar replica set local**

O `docker-compose.yml` deve iniciar um MongoDB com `--replSet rs0`, healthcheck `mongosh --eval "db.adminCommand({ ping: 1 })"` e script de inicialização que execute `rs.initiate()` uma única vez.

- [ ] **Passo 4: Implementar cliente server-side**

Ler `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` exclusivamente no backend. Recusar inicialização quando a URI ou o database não existir.

- [ ] **Passo 5: Rodar teste e healthcheck**

Executar: `cd apps/api; python -m pytest -q`; depois `docker compose -f infra/mongodb/docker-compose.yml up -d` e `curl http://127.0.0.1:8000/health`.

- [ ] **Passo 6: Commitar fundação**

```bash
git add apps/api infra/mongodb README.md .gitignore
git commit -m "feat(gerec-leads): cria API Python e MongoDB local"
```

### Tarefa 3: Criar coleções, validações e índices MongoDB

**Arquivos:**
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py`
- Criar: `apps/api/tests/integration/test_indexes.py`
- Criar: `scripts/mongodb-bootstrap.ps1`

**Interfaces:**
- `ensure_schema(db) -> None`
- `collection(db, name) -> Collection`
- `MongoCollections` expõe nomes canônicos sem queries espalhadas.

- [ ] **Passo 1: Escrever testes vermelhos de índices**

Verificar índices únicos para `users.emailNormalized`, `source_records.sourceLeadId`, `companies.documentNormalized`, `leads(companyId,campaignId,archivedAt)`, `sales.leadId`, `sessions.tokenHash` e idempotência por comando.

- [ ] **Passo 2: Implementar validações e índices**

Criar índices com `unique=True` e índices parciais para documentos presentes, leads não arquivados e vendas não revertidas. Criar validação de documento via código de domínio antes da persistência.

- [ ] **Passo 3: Implementar bootstrap idempotente**

`ensure_schema` cria/atualiza índices sem apagar coleções nem dados. O script local deve poder ser executado repetidamente.

- [ ] **Passo 4: Rodar testes contra replica set**

Executar: `docker compose -f infra/mongodb/docker-compose.yml up -d`; `cd apps/api; python -m pytest tests/integration/test_indexes.py -q`.

- [ ] **Passo 5: Commitar schema Mongo**

```bash
git add apps/api/src/gerec_api/infrastructure/mongo apps/api/tests/integration scripts/mongodb-bootstrap.ps1
git commit -m "feat(gerec-leads): define coleções e índices MongoDB"
```

### Tarefa 4: Implementar autenticação e sessões no MongoDB

**Arquivos:**
- Criar: `apps/api/src/gerec_api/auth/passwords.py`
- Criar: `apps/api/src/gerec_api/auth/sessions.py`
- Criar: `apps/api/src/gerec_api/auth/dependencies.py`
- Criar: `apps/api/src/gerec_api/routes/auth.py`
- Criar: `apps/api/tests/unit/test_passwords.py`
- Criar: `apps/api/tests/integration/test_auth.py`

**Interfaces:**
- `hash_password(password: str) -> str`
- `verify_password(password: str, digest: str) -> bool`
- `AuthService.login(email: str, password: str) -> SessionResult`
- `AuthService.logout(raw_token: str) -> None`
- `get_current_user(request: Request) -> CurrentUser`

- [ ] **Passo 1: Escrever testes vermelhos**

Cobrir senha nunca armazenada em texto puro, login válido/inválido, cookie `httpOnly`, expiração, logout, revogação e usuário desativado sem acesso.

- [ ] **Passo 2: Implementar hash e sessão opaca**

Usar Argon2id. Gerar token aleatório, persistir somente `sha256(token)`, guardar `userId`, `expiresAt`, `revokedAt` e timestamps.

- [ ] **Passo 3: Implementar rotas**

Criar `POST /auth/login`, `POST /auth/logout` e `GET /auth/me`. A API define cookie seguro e nunca retorna digest, senha ou segredo.

- [ ] **Passo 4: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/unit/test_passwords.py tests/integration/test_auth.py -q`.

- [ ] **Passo 5: Commitar autenticação**

```bash
git add apps/api/src/gerec_api/auth apps/api/src/gerec_api/routes/auth.py apps/api/tests
git commit -m "feat(gerec-leads): adiciona autenticação MongoDB"
```

### Tarefa 5: Implementar módulo profundo de leads e importação idempotente

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/leads.py`
- Criar: `apps/api/src/gerec_api/domain/normalization.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`
- Criar: `apps/api/src/gerec_api/automation/workbook_adapter.py`
- Criar: `apps/api/src/gerec_api/routes/leads.py`
- Criar: `apps/api/tests/unit/test_normalization.py`
- Criar: `apps/api/tests/integration/test_import.py`

**Interfaces:**
- `normalize_source_row(row: dict) -> NormalizedSourceRow`
- `LeadService.import_row(row: NormalizedSourceRow, idempotency_key: str) -> ImportResult`
- `LeadService.archive_missing(source_snapshot_id: str) -> ArchiveResult`
- `WorkbookAdapter.read(path: Path) -> Iterable[NormalizedSourceRow]`

- [ ] **Passo 1: Escrever testes vermelhos**

Cobrir normalização de documento, telefone, e-mail, estado, datas, headers A–Q, projeção M–P, exclusão de Q, M não interpretada como CNPJ, mesma origem repetida, mesma empresa/campanha e linha removida.

- [ ] **Passo 2: Implementar adapter do workbook**

Ler somente a aba `Leads`, validar headers exatos A–Q e transformar a resposta M em campo informativo. O adapter não cria CNPJ a partir de M.

- [ ] **Passo 3: Implementar importação transacional**

Dentro de `with_transaction`, criar ou atualizar `source_records`, resolver campanha/empresa, criar/atualizar `leads` e gravar resultado idempotente. Pendências de documento/campanha não entram na fila.

- [ ] **Passo 4: Implementar snapshot e arquivamento**

Marcar origem ausente como arquivada; arquivar ocorrência somente quando não houver outra origem ativa. Preservar histórico.

- [ ] **Passo 5: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/unit/test_normalization.py tests/integration/test_import.py -q`.

- [ ] **Passo 6: Commitar leads e adapter**

```bash
git add apps/api/src/gerec_api/domain/leads.py apps/api/src/gerec_api/domain/normalization.py apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py apps/api/src/gerec_api/automation/workbook_adapter.py apps/api/src/gerec_api/routes/leads.py apps/api/tests
git commit -m "feat(gerec-leads): implementa leads e importação MongoDB"
```

### Tarefa 6: Implementar fila transacional, propriedade e créditos

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/queue.py`
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`
- Criar: `apps/api/src/gerec_api/routes/queue.py`
- Criar: `apps/api/tests/unit/test_queue_rules.py`
- Criar: `apps/api/tests/integration/test_queue_transactions.py`
- Criar: `apps/api/tests/integration/test_queue_concurrency.py`

**Interfaces:**
- `QueueService.distribute_normal(lead_id: ObjectId, command_id: str) -> AssignmentResult`
- `QueueService.assign_recurring(lead_id: ObjectId, command_id: str) -> AssignmentResult`
- `QueueService.assign_temporarily(lead_id: ObjectId, seller_id: ObjectId, reason: str, command_id: str) -> AssignmentResult`
- `QueueService.transfer_owner(company_id: ObjectId, seller_id: ObjectId, reason: str, command_id: str) -> TransferResult`

- [ ] **Passo 1: Escrever testes vermelhos dos critérios AC-01 a AC-11 e AC-29**

Testar rodízio Renato/Sandra/Jessica/Nelma, perda de vez, bloqueio por um atraso, todos bloqueados, FIFO, recorrência, créditos atravessando rotações, proprietário bloqueado, direcionamento temporário, transferência e concorrência.

- [ ] **Passo 2: Implementar transação da fila**

Bloquear `queue_state` com atualização versionada dentro de sessão MongoDB. Em uma transação, avaliar elegibilidade, consumir crédito, criar assignment, atualizar lead, gravar auditoria e outbox.

- [ ] **Passo 3: Implementar propriedade**

O primeiro assignment efetivo define `companies.ownerId`. Recorrência direciona ao proprietário sem mover cursor e cria crédito. Venda temporária preserva proprietário.

- [ ] **Passo 4: Implementar testes concorrentes**

Executar duas transações simultâneas sobre leads diferentes e verificar assignments únicos, cursor equivalente ao sequencial e nenhum saldo negativo.

- [ ] **Passo 5: Commitar fila**

```bash
git add apps/api/src/gerec_api/domain/queue.py apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py apps/api/src/gerec_api/routes/queue.py apps/api/tests
git commit -m "feat(gerec-leads): implementa fila transacional MongoDB"
```

### Tarefa 7: Implementar calendário útil, SLA, feedbacks, tentativas e resultados

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/business_time.py`
- Criar: `apps/api/src/gerec_api/domain/operations.py`
- Criar: `apps/api/src/gerec_api/routes/operations.py`
- Criar: `apps/api/tests/unit/test_business_time.py`
- Criar: `apps/api/tests/unit/test_operations.py`
- Criar: `apps/api/tests/integration/test_operations_transactions.py`

**Interfaces:**
- `BusinessClock.add_business_hours(start: datetime, hours: int) -> datetime`
- `OperationsService.register_feedback(command) -> FeedbackResult`
- `OperationsService.register_attempt(command) -> AttemptResult`
- `OperationsService.register_outcome(command) -> OutcomeResult`

- [ ] **Passo 1: Escrever testes vermelhos AC-18 a AC-24, AC-28 e AC-30**

Cobrir 24 horas úteis, lembrete em 4 horas úteis, feriados nacionais/SP, comentário mínimo, uma tentativa por dia útil, cinco dias distintos, desqualificação manual, não conversão, venda única e nota administrativa sem desbloqueio.

- [ ] **Passo 2: Implementar relógio injetável**

Toda regra recebe `Clock.now()` e `HolidayRepository`; nenhum teste usa horário real. Dias não úteis são ignorados integralmente.

- [ ] **Passo 3: Implementar comandos transacionais**

Feedback válido fecha ciclo anterior e abre o próximo. Tentativa valida dia útil distinto, comentário e limite. Resultado final encerra SLA, cria evento e, em `won`, cria uma única venda e marca empresa cliente.

- [ ] **Passo 4: Rodar testes de operação**

Executar: `cd apps/api; python -m pytest tests/unit/test_business_time.py tests/unit/test_operations.py tests/integration/test_operations_transactions.py -q`.

- [ ] **Passo 5: Commitar operações**

```bash
git add apps/api/src/gerec_api/domain/business_time.py apps/api/src/gerec_api/domain/operations.py apps/api/src/gerec_api/routes/operations.py apps/api/tests
git commit -m "feat(gerec-leads): implementa SLA feedbacks e resultados"
```

### Tarefa 8: Completar autorização, leituras e auditoria

**Arquivos:**
- Criar: `apps/api/src/gerec_api/auth/permissions.py`
- Criar: `apps/api/src/gerec_api/routes/dashboard.py`
- Criar: `apps/api/src/gerec_api/routes/admin.py`
- Criar: `apps/api/tests/integration/test_permissions.py`
- Criar: `apps/api/tests/integration/test_audit.py`

**Interfaces:**
- `PermissionService.require_admin(user) -> None`
- `PermissionService.scope_query(user, resource) -> MongoFilter`
- `DashboardService.for_user(user) -> DashboardPayload`

- [ ] **Passo 1: Escrever testes vermelhos de isolamento**

Verificar que vendedor só lê leads próprios, históricos permitidos e saldo próprio; admin lê global; vendedor não executa comandos administrativos; usuário desativado falha mesmo com sessão antiga; chamadas diretas não atravessam escopo.

- [ ] **Passo 2: Implementar filtros server-side**

Toda query recebe `CurrentUser`; repositórios recusam filtro ausente. Não há endpoint que aceite `sellerId` arbitrário para ampliar escopo.

- [ ] **Passo 3: Implementar dashboard e administração**

Expor leituras paginadas para leads, fila, histórico e usuários; ações administrativas chamam comandos de domínio, nunca atualizações diretas de documentos sensíveis.

- [ ] **Passo 4: Validar auditoria**

Cada comando grava ator, ação, entidade, antes/depois, timestamp e correlation ID na mesma transação.

- [ ] **Passo 5: Commitar autorização**

```bash
git add apps/api/src/gerec_api/auth apps/api/src/gerec_api/routes apps/api/tests
git commit -m "feat(gerec-leads): aplica autorização e auditoria no backend"
```

### Tarefa 9: Adaptar o site Next.js para a API Python

**Arquivos:**
- Criar: `apps/web/src/lib/api/client.ts`
- Criar: `apps/web/src/lib/api/types.ts`
- Modificar: `apps/web/src/lib/auth/actions.ts`
- Modificar: `apps/web/src/lib/auth/get-session-context.ts`
- Modificar: `apps/web/src/lib/dashboard/queries.ts`
- Modificar: `apps/web/src/lib/operations/actions.ts`
- Modificar: `apps/web/src/lib/admin/**/*.ts`
- Modificar: páginas e componentes que atualmente assumem Supabase
- Remover após cobertura equivalente: `apps/web/src/lib/supabase/`
- Teste: `apps/web/src/lib/api/client.test.ts`

**Interfaces:**
- `apiFetch<T>(path, init?) -> Promise<T>`
- `getSessionContext() -> AuthenticatedSession`
- Server actions chamam endpoints Python e nunca conhecem MongoDB.

- [ ] **Passo 1: Escrever testes vermelhos do cliente HTTP**

Cobrir propagação de cookies, erro 401 para `/login`, erro 403, payload de validação e ausência de URI MongoDB no bundle.

- [ ] **Passo 2: Substituir login/sessão**

Usar `NEXT_PUBLIC_API_URL` somente para a URL pública da API. O site não recebe segredos e não monta queries MongoDB.

- [ ] **Passo 3: Substituir leituras**

Trocar consultas PostgREST por endpoints paginados Python. Preservar componentes, textos pt-BR, estado demo apenas em ambiente local explicitamente habilitado.

- [ ] **Passo 4: Substituir ações**

Feedback, tentativa, resultado, arquivamento, usuários e simulação chamam comandos Python idempotentes. Remover updates diretos e fallback demo em staging/produção.

- [ ] **Passo 5: Rodar testes web**

Executar: `npm --workspace @wtg/web run test`, `npm --workspace @wtg/web run typecheck`, `npm --workspace @wtg/web run lint`.

- [ ] **Passo 6: Commitar integração Vercel**

```bash
git add apps/web
git commit -m "feat(gerec-leads): conecta site Vercel à API Python"
```

### Tarefa 10: Implementar automações Python na Railway

**Arquivos:**
- Criar: `apps/api/src/gerec_api/automation/sync_job.py`
- Criar: `apps/api/src/gerec_api/automation/outbox_worker.py`
- Criar: `apps/api/src/gerec_api/automation/scheduler.py`
- Criar: `apps/api/tests/integration/test_automation_idempotency.py`
- Criar: `railway.json`
- Modificar: `integrations/n8n/README.md` para documentar remoção do n8n

**Interfaces:**
- `run_sync(source: SourceAdapter, run_id: str) -> SyncResult`
- `process_outbox(batch_size: int) -> int`
- `run_due_jobs(now: datetime) -> JobResult`

- [ ] **Passo 1: Escrever testes vermelhos**

Testar sync a cada 5 minutos, repetição segura, snapshot completo, outbox idempotente, retry de e-mail e não duplicação de alertas.

- [ ] **Passo 2: Implementar worker**

O worker usa os mesmos serviços de domínio da API, executa jobs com lock/idempotência no MongoDB e não duplica atribuições.

- [ ] **Passo 3: Configurar Railway**

Definir um serviço web para a API Python e um worker/cron Python para automações, com variáveis `MONGODB_URI`, `MONGODB_DATABASE`, `APP_SECRET` e credenciais externas somente na Railway.

- [ ] **Passo 4: Rodar testes**

Executar: `cd apps/api; python -m pytest tests/integration/test_automation_idempotency.py -q`.

- [ ] **Passo 5: Commitar automações**

```bash
git add apps/api/src/gerec_api/automation railway.json integrations/n8n/README.md apps/api/tests
git commit -m "feat(gerec-leads): move automações para Python Railway"
```

### Tarefa 11: Configurar deploy Vercel, contratos e E2E

**Arquivos:**
- Criar: `vercel.json`
- Modificar: `playwright.config.ts`
- Modificar: `tests/e2e/*.spec.ts`
- Criar: `tests/e2e/auth.spec.ts`
- Criar: `tests/e2e/roles.spec.ts`
- Criar: `tests/e2e/lead-lifecycle.spec.ts`
- Modificar: `.github/workflows/gerec-leads-ci.yml`
- Criar: `tests/contracts/api-contracts.test.mjs`

**Interfaces produzidas:** contrato HTTP versionado entre Vercel e Railway e suíte E2E dos dois perfis.

- [ ] **Passo 1: Atualizar teste E2E legado**

Substituir o teste que espera o antigo health check por login, dashboard e indicação da API conectada.

- [ ] **Passo 2: Escrever contratos HTTP**

Validar status, payloads, erros e campos mínimos de `/auth`, `/leads`, `/queue`, `/operations` e `/admin`.

- [ ] **Passo 3: Escrever E2E de isolamento e ciclo**

Cobrir admin global, vendedor privado, usuário desativado, novo → contato → qualificado → ganho, cinco tentativas e venda única.

- [ ] **Passo 4: Configurar CI**

O CI deve iniciar MongoDB replica set, API Python, site Next.js, executar testes Python/TypeScript/E2E e derrubar serviços com `if: always()`.

- [ ] **Passo 5: Rodar suíte completa**

Executar: `python -m pytest apps/api/tests -q`; `npm run check`; `npm run test:e2e`.

- [ ] **Passo 6: Commitar deploy e contratos**

```bash
git add vercel.json playwright.config.ts tests .github/workflows/gerec-leads-ci.yml
git commit -m "test(gerec-leads): valida contratos Vercel Railway e E2E"
```

### Tarefa 12: Remover Supabase e fechar documentação operacional

**Arquivos:**
- Remover após cobertura equivalente: `supabase/`, `tooling/supabase/`
- Modificar: `package.json`, `package-lock.json`, `README.md`, `apps/web/.env.example`
- Criar: `apps/api/.env.example`
- Modificar: `docs/evidencias/etapa-2.md` ou criar evidência da migração

**Interfaces produzidas:** comandos locais reproduzíveis para MongoDB, API Python, site e workers.

- [ ] **Passo 1: Confirmar ausência de dependências Supabase**

Executar `rg -n -i "supabase|service_role|postgres|postgrest" --glob '!docs/superpowers/specs/**' --glob '!docs/superpowers/plans/**'` e resolver cada ocorrência de runtime, teste e documentação operacional.

- [ ] **Passo 2: Atualizar comandos**

Substituir scripts Supabase por scripts PowerShell versionados: iniciar replica set, executar bootstrap Mongo, iniciar API, iniciar web e executar worker.

- [ ] **Passo 3: Validar secrets**

Garantir que somente `MONGODB_URI`, `MONGODB_DATABASE` e `APP_SECRET` server-side existam no backend; a Vercel recebe apenas `NEXT_PUBLIC_API_URL`.

- [ ] **Passo 4: Rodar verificação final**

Executar `git diff --check`, testes Python, testes web, contratos, build e E2E. Confirmar `git status --short` limpo após o commit.

- [ ] **Passo 5: Commitar remoção**

```bash
git add -A
git commit -m "refactor(gerec-leads): remove dependência do Supabase"
```

## Gate final

A migração só será considerada concluída quando:

- a API Python funcionar localmente e na Railway;
- o site funcionar pela URL da Vercel;
- MongoDB for o único banco usado em runtime;
- não houver dependência de Supabase no código operacional;
- fila, SLA, recorrência, permissões, venda única e auditoria tiverem testes passando;
- CI, backup, restauração e E2E dos dois perfis estiverem validados;
- nenhuma credencial aparecer no bundle, logs ou repositório;
- as limitações e evidências estiverem registradas na documentação.
