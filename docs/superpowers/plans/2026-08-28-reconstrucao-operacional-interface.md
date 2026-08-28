# Reconstrução operacional do Gerenciador de Leads — Plano de implementação

> **Para agentes de implementação:** SUB-SKILL OBRIGATÓRIA: usar `subagent-driven-development` para executar este plano tarefa a tarefa. Todas as tarefas usam checklist e exigem revisão independente antes do próximo commit.

**Objetivo:** transformar o sistema implantado em uma operação desktop funcional, na qual o vendedor trata somente seus leads e o administrador administra usuários e consulta a operação sem alterar a tratativa.

**Arquitetura:** regras de calendário, situação comercial, disponibilidade e rodízio permanecem no backend Python, dentro de comandos transacionais MongoDB. A API retorna projeções distintas por papel; o Next.js apenas exibe dados e envia intenções autenticadas. A mudança começa por governança, contrato e testes de domínio, prossegue para persistência/API e só então para interface e E2E visual.

**Tecnologias:** Python 3.12, FastAPI, Pydantic, PyMongo/MongoDB Replica Set, Argon2id, Next.js/React/TypeScript, Vitest, Playwright e Railway/Vercel.

**Fontes de verdade:** `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`, `docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md`, `AGENTS.md`.

## Restrições globais

- Interface exclusivamente desktop; mínimo suportado 1280 px e validação de referência em 1440 × 900.
- Todo texto novo é em português do Brasil; IDs MongoDB não são rótulos principais na interface.
- Google Sheets permanece somente origem; M–P são a projeção de origem permitida ao vendedor e Q continua excluída.
- MongoDB é a única persistência; toda escrita crítica usa transação em replica set, escrita condicional e idempotency key.
- Nenhum segredo, URI MongoDB, hash ou senha chega ao navegador, às respostas API ou aos logs.
- Vendedor não recebe dados de outros vendedores; administrador pode ler globalmente, mas não cria nem altera tratativas, status ou responsável neste corte.
- SLA: 24 horas úteis em `America/Sao_Paulo`, segunda–sexta, exceto feriado nacional/estadual de SP, dentro de `[09:00,18:00)`; lembrete em quatro horas úteis antes do vencimento.
- Situação primária obrigatória em toda tratativa: `undefined`, `negotiation` ou `won`; `isDisqualified` é marcador adicional, exige comentário e encerra SLA sem reabri-lo automaticamente.
- Comentário útil tem ao menos 6 caracteres; vendedor atual é o único autor possível.
- Vendedor recém-criado ativo entra no final da fila; administrador não entra; pausa manual não transfere leads; reset de senha revoga todas as sessões.
- O estado real da fila é derivado de ordem persistida + cursor + disponibilidade: `Ativo`, `Pausado` ou `Bloqueado por atraso`.
- Não alterar arquivos locais alheios já pendentes: `apps/api/.env.example` removido e `tools/google-sheets-diagnostic/` não rastreado.

## Estrutura de arquivos e responsabilidades

| Área | Arquivos principais | Responsabilidade |
| --- | --- | --- |
| Governança | `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/DECISOES.md`, desenho e contexto mestre | Registrar a substituição explícita de regras canônicas antes da implementação. |
| Tempo | `apps/api/src/gerec_api/domain/business_time.py` | Calcular apenas tempo útil dentro da janela comercial e com relógio controlável. |
| Tratativa | `apps/api/src/gerec_api/domain/operations.py`, `infrastructure/mongo/operations_repository.py` | Validar, gravar atomicamente e projetar comentários/status/marcador/SLA. |
| Usuários e sessão | `auth/sessions.py`, novo módulo de administração e `routes/admin.py` | Criar usuários, pausar/ativar vendedores, redefinir senha e revogar sessões. |
| Fila | `domain/queue.py`, `infrastructure/mongo/queue_repository.py` | Derivar disponibilidade, inserir vendedores e expor cursor/ordem dinâmica. |
| Leitura | `auth/permissions.py`, `routes/dashboard.py`, `routes/leads.py` | Contratos seguros e enriquecidos para administrador e vendedor. |
| Interface | `apps/web/src/app/**`, `components/**`, `lib/api/**` | Controles reais, páginas por papel, modais e apresentação desktop. |
| Verificação | `apps/api/tests/**`, `apps/web/src/**/*.test.ts`, `tests/contracts/**`, `tests/e2e/**` | Testes unitários, integração, contratos, E2E e screenshots determinísticas. |

---

### Task 1 — Registrar a governança da reconstrução

**Arquivos:**
- Modificar: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` (seção 39; criar `GOV-004`).
- Modificar: `docs/DECISOES.md` (criar `DEC-028`).
- Modificar: `docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md`.
- Modificar: `scripts/generate-master-context.ps1` somente se novos documentos não forem incluídos automaticamente.
- Gerar: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

**Consome:** decisões aprovadas no desenho de 28/08.

**Produz:** governança canônica para todas as tarefas seguintes.

- [ ] **Passo 1: Escrever a verificação documental que deve falhar.**

Criar em `tests/contracts/spec-governance.test.mjs` verificações textuais para `GOV-004` e `DEC-028`, exigindo as expressões `09:00`, `18:00`, `Bloqueado por atraso`, `isDisqualified`, `senha não vazia`, `comentário` e `Yago, André, Renato, Sandra, Jessica e Nelma`.

- [ ] **Passo 2: Executar a verificação vermelha.**

Executar: `node --test tests/contracts/spec-governance.test.mjs`

Esperado: falha porque `GOV-004` e `DEC-028` ainda não existem.

- [ ] **Passo 3: Registrar a alteração aprovada.**

Inserir `GOV-004 — Operação comercial, SLA e permissões` com a regra anterior, regra nova, motivo, impactos em dados/métricas, migração e aceite. Registrar também que as contas iniciais configuradas neste ambiente são Yago e André administradores; Renato, Sandra, Jessica e Nelma vendedores. Em `DEC-028`, repetir a decisão sem contradizer GOV-004. Marcar o desenho como aprovado para implementação e regenerar o contexto mestre.

- [ ] **Passo 4: Executar a verificação verde.**

Executar: `node --test tests/contracts/spec-governance.test.mjs; powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`

Esperado: teste verde e contexto mestre contendo `GOV-004` e `DEC-028`.

- [ ] **Passo 5: Revisar e versionar.**

Executar: `git diff --check` e `git diff -- SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/DECISOES.md docs/superpowers/specs/2026-08-28-reconstrucao-interacoes-sla-design.md docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

Commit: `docs(gerec-leads): formaliza reconstrução operacional`

### Task 2 — Corrigir o calendário de horas úteis por TDD

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/business_time.py`.
- Modificar: `apps/api/tests/unit/test_business_time.py`.

**Consome:** GOV-004.

**Produz:** `add_business_hours(start_at, hours, calendar)` e `subtract_business_hours(deadline_at, hours, calendar)` corretos dentro de `[09:00,18:00)`.

- [ ] **Passo 1: Escrever testes de borda controlados.**

Adicionar casos explícitos: sexta 17:00 + 24h = quarta útil seguinte 14:00; 08:30 inicia às 09:00; 18:00 inicia às 09:00 do próximo dia útil; 17:59 preserva um minuto; travessia de sábado/domingo; feriado estadual de SP; lembrete calculado com subtração de quatro horas úteis.

- [ ] **Passo 2: Executar a suíte vermelha.**

Executar: `python -m pytest apps/api/tests/unit/test_business_time.py -q`

Esperado: falhas que revelem o limite atual em meia-noite.

- [ ] **Passo 3: Implementar o cálculo mínimo.**

Normalizar a entrada para o próximo instante elegível, consumir somente o intervalo até 18:00 e pular para 09:00 do próximo dia elegível quando necessário. Reutilizar o mesmo predicado de dia útil em soma e subtração; manter timezone aware e sem acessar relógio real.

- [ ] **Passo 4: Executar a suíte verde.**

Executar: `python -m pytest apps/api/tests/unit/test_business_time.py -q`

Esperado: todos os casos de janela, fim de semana e feriado verdes.

- [ ] **Passo 5: Versionar.**

Commit: `fix(gerec-leads): calcula SLA na janela comercial`

### Task 3 — Versionar schema e migração idempotente de reconstrução

**Arquivos:**
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260828_operacao_comercial.py`.
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/collections.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py`.
- Criar: `apps/api/tests/integration/test_operational_migration.py`.

**Consome:** calendário da Tarefa 2 e documentos existentes de leads, assignments, feedbacks, queue state e usuários.

**Produz:** coleção `lead_treatments`; campos de projeção em `leads`; índices de fila, tratativa e idempotência; registro de migração aplicado.

- [ ] **Passo 1: Escrever testes de migração.**

Criar fixture com lead legado, assignment, feedback legado, sessão e posição de fila. Exigir que a primeira execução materialize `commercialStatus`, `isDisqualified`, `commentCount`, `lastCommentAt`, `feedbackDueAt`, `feedbackReminderAt`; que a segunda execução não altere resultado; que não apague eventos ou sessões; e que índices únicos sejam criados.

- [ ] **Passo 2: Executar o teste vermelho.**

Executar: `python -m pytest apps/api/tests/integration/test_operational_migration.py -q`

Esperado: falha por ausência de runner/migração.

- [ ] **Passo 3: Implementar migração idempotente.**

Adicionar `schema_migrations` com identificador único. Converter outcomes antigos para `commercialStatus`, preservar `isDisqualified` quando outcome legado for desqualificado, contar somente eventos de comentário válidos, recalcular ciclos abertos pela Tarefa 2 e criar índices: `lead_treatments(leadId, createdAt)`, chave única `lead_treatments(leadId, idempotencyKey)`, `seller_queue(sellerId)` e posição única parcial/validada conforme capacidade do Mongo.

- [ ] **Passo 4: Executar integração verde.**

Executar: `python -m pytest apps/api/tests/integration/test_operational_migration.py apps/api/tests/integration/test_indexes.py -q`

Esperado: migração repetível sem perda de histórico.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): versiona schema operacional`

### Task 4 — Implementar o comando transacional de tratativa

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/operations.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py`.
- Criar: `apps/api/tests/unit/test_treatment_rules.py`.
- Modificar: `apps/api/tests/integration/test_operations_transactions.py`.

**Interface produzida:**

```python
TreatmentCommand(
    lead_id: ObjectId,
    comment: str,
    commercial_status: Literal["undefined", "negotiation", "won"],
    is_disqualified: bool,
    idempotency_key: str,
)
OperationsService.with_actor(...).register_treatment(command) -> TreatmentResult
```

- [ ] **Passo 1: Escrever testes vermelhos de regra e transação.**

Cobrir: cinco caracteres falham; situação ausente falha; desqualificado sem comentário falha; vendedor não responsável recebe negação; admin recebe negação; comentário válido atualiza campos e cria evento; `won + isDisqualified=True` é aceito; reenvio com mesma chave não duplica contador; falha intermediária faz rollback de evento, lead, auditoria e ciclo.

- [ ] **Passo 2: Executar os testes vermelhos.**

Executar: `python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q`

Esperado: falhas porque o comando e a projeção ainda não existem.

- [ ] **Passo 3: Implementar o comando mínimo.**

Validar texto útil com `strip()`, validar situação fechada, conferir dono atual e papel seller. Na transação: gravar `lead_treatments` imutável, atualizar projeção do lead e auditoria. Para marcador desqualificado, definir `feedbackDueAt`/`feedbackReminderAt` como `null` e fechar ciclo; nos demais casos abrir/renovar SLA pela Tarefa 2. Nunca permitir endpoint administrativo para esse comando.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q`

Esperado: invariantes, idempotência e rollback verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): registra tratativa comercial imutável`

### Task 5 — Implementar disponibilidade e rotação real da fila

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/domain/queue.py`.
- Modificar: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`.
- Modificar: `apps/api/tests/unit/test_queue_rules.py`.
- Modificar: `apps/api/tests/integration/test_queue_transactions.py`.
- Modificar: `apps/api/tests/integration/test_queue_concurrency.py`.

**Interface produzida:**

```python
SellerAvailability(status: Literal["active", "paused", "blocked_overdue"], reason: str | None)
QueueSnapshot(cursor_seller_id: ObjectId | None, entries: list[QueueEntry])
```

- [ ] **Passo 1: Escrever testes vermelhos de disponibilidade.**

Cobrir: lead vencido bloqueia vendedor, desqualificado não bloqueia, regularização de todos remove apenas bloqueio automático, pausa continua após regularização, pausa preserva leads, cursor avança sobre indisponíveis e a lista apresentada começa no próximo elegível. Cobrir concorrência para que duas distribuições preservem uma única ordem/cursor.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q`

Esperado: falhas nas projeções de motivo/cursor e no efeito do novo SLA.

- [ ] **Passo 3: Implementar cálculo único de disponibilidade.**

Criar uma única função que prioriza `paused` sobre `blocked_overdue`, deriva atraso de ciclos abertos e retorna `active` caso contrário. Ordenar leitura por `position` circular a partir de `queue_state.nextSellerId`, sem usar ordem de `createdAt`; após atribuição persistir cursor do próximo participante elegível e nunca restaurar turnos perdidos.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/unit/test_queue_rules.py apps/api/tests/integration/test_queue_transactions.py apps/api/tests/integration/test_queue_concurrency.py -q`

Esperado: rodízio dinâmico, pausa e bloqueio demonstrados em transação.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): deriva fila pela disponibilidade real`

### Task 6 — Implementar comandos administrativos de usuários e sessões

**Arquivos:**
- Criar: `apps/api/src/gerec_api/domain/user_administration.py`.
- Criar: `apps/api/src/gerec_api/infrastructure/mongo/user_repository.py`.
- Modificar: `apps/api/src/gerec_api/auth/sessions.py`.
- Modificar: `apps/api/src/gerec_api/routes/admin.py`.
- Modificar: `apps/api/tests/integration/test_auth.py`.
- Criar: `apps/api/tests/integration/test_user_administration.py`.

**Interface produzida:**

```text
POST /api/admin/users {fullName, email, role, password}
PATCH /api/admin/users/{id}/availability {paused}
PATCH /api/admin/users/{id}/password {password}
```

- [ ] **Passo 1: Escrever testes vermelhos.**

Cobrir admin cria usuário com senha não vazia, e-mail único, resposta sem hash/senha, novo seller ativo entra na última posição, novo admin não entra na fila, pausa/ativação não transfere leads, vendedor recebe 403, reset invalida dois tokens existentes e senha antiga deixa de autenticar.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/integration/test_user_administration.py apps/api/tests/integration/test_auth.py -q`

Esperado: falhas por ausência dos comandos e revogação em massa.

- [ ] **Passo 3: Implementar serviços e rotas finas.**

Usar Argon2id já existente. Rejeitar somente senha vazia após `strip()`; não aplicar mínimo/composição. Dentro da transação de criação, inserir usuário e, se seller ativo, calcular `max(position)+1` com proteção contra concorrência. No reset, trocar hash e revogar todas as sessões por `userId`; retornar somente metadados públicos. Registrar auditoria sem senha.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/integration/test_user_administration.py apps/api/tests/integration/test_auth.py -q`

Esperado: CRUD restrito ao admin e sessões antigas inválidas.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): administra usuários e sessões`

### Task 7 — Separar contratos de leitura por papel

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/auth/permissions.py`.
- Modificar: `apps/api/src/gerec_api/routes/dashboard.py`.
- Modificar: `apps/api/src/gerec_api/routes/leads.py`.
- Modificar: `apps/api/src/gerec_api/routes/queue.py`.
- Criar: `apps/api/tests/integration/test_operational_read_models.py`.

**Interface produzida:**

```text
GET /api/dashboard
GET /api/leads/{id}/treatments?page=&limit=
GET /api/queue
```

Admin recebe leads globais, fila completa e histórico de tratativas somente leitura. Seller recebe somente seus leads, suas tratativas e sua própria posição/estado, sem `nextSellerName`, lista ou contagem de colegas.

- [ ] **Passo 1: Escrever testes vermelhos.**

Exigir campos legíveis no lead: `contactName`, `sellerName`, `companyName`, `campaignName`, `phoneDisplay`, `email`, `commercialStatus`, `isDisqualified`, `commentCount`, `feedbackDueAt`. Exigir fallback `Não informado`; admin lê tratamentos; seller A não lê lead/tratamento/fila de B e não recebe `nextSellerName`.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `python -m pytest apps/api/tests/integration/test_permissions.py apps/api/tests/integration/test_operational_read_models.py -q`

Esperado: falhas por campos ausentes e vazamento de fila global.

- [ ] **Passo 3: Implementar projeções.**

Separar explicitamente `for_admin` e `for_seller`; resolver nomes server-side, normalizar telefone removendo prefixo nacional `55`, formatar apenas no web, retirar IDs públicos não necessários e expor motivo de indisponibilidade/cursor somente ao admin. Ordenar histórico de tratativas por data decrescente e paginar no servidor.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `python -m pytest apps/api/tests/integration/test_permissions.py apps/api/tests/integration/test_operational_read_models.py -q`

Esperado: escopo de vendedor e leitura administrativa seguros.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): separa leituras administrativas e vendedor`

### Task 8 — Expor a tratativa pela API e retirar comandos conflitantes

**Arquivos:**
- Modificar: `apps/api/src/gerec_api/routes/operations.py`.
- Modificar: `apps/api/src/gerec_api/main.py` se for necessário registrar novas dependências.
- Modificar: `tests/contracts/api-contract-server.py`.
- Modificar: `tests/contracts/api-contracts.test.mjs`.

**Interface produzida:**

```text
POST /api/leads/{leadId}/treatments
{ comment, commercialStatus, isDisqualified, idempotencyKey }
```

- [ ] **Passo 1: Escrever contrato vermelho.**

Adicionar exemplos 201/422/403/409: sucesso, comentário curto, status inválido, admin proibido, seller sem propriedade proibido e reenvio idempotente. Declarar que `/api/admin/leads/{id}/notes` não faz parte do contrato operacional novo.

- [ ] **Passo 2: Executar contrato vermelho.**

Executar: `node --test tests/contracts/api-contracts.test.mjs`

Esperado: falha até a rota e os exemplos existirem.

- [ ] **Passo 3: Implementar boundary fino.**

Criar `TreatmentRequest` Pydantic com `min_length=6`, enum fechado e chave idempotente. Chamar somente `OperationsService.register_treatment`; mapear validação para 422, autorização para 403 e conflito para 409. Remover rota de nota administrativa e não reutilizar endpoint de tentativas para comentário.

- [ ] **Passo 4: Executar contrato e API verde.**

Executar: `node --test tests/contracts/api-contracts.test.mjs; python -m pytest apps/api/tests/integration/test_operations_transactions.py apps/api/tests/integration/test_permissions.py -q`

Esperado: contrato HTTP e políticas verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): expõe tratativa segura na API`

### Task 9 — Tipos web, cliente HTTP e formatação de apresentação

**Arquivos:**
- Modificar: `apps/web/src/lib/api/types.ts`.
- Modificar: `apps/web/src/lib/api/client.ts`.
- Modificar: `apps/web/src/lib/dashboard/queries.ts`.
- Modificar: `apps/web/src/lib/dashboard/format.ts`.
- Modificar: testes correspondentes em `apps/web/src/lib/**/*.test.ts`.

**Produz:** tipos separados `AdminDashboard`, `SellerDashboard`, `OperationalLead`, `Treatment`, `QueueEntry`, `ManagedUser`; chamadas HTTP para usuários, disponibilidade, senha, tratativa e histórico.

- [ ] **Passo 1: Escrever testes vermelhos.**

Cobrir mapeamento de `commercialStatus`, marcador, contador, prazo, `Não informado`, telefone `5511988308029 → (11) 98830-8029`, data em `America/Sao_Paulo` e serialização das requisições de tratativa/usuário sem senha em retorno.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run`

Esperado: tipos/clientes ausentes ou incompatíveis com o contrato novo.

- [ ] **Passo 3: Implementar o cliente tipado.**

Centralizar `apiFetch`, tratar 401/403/409/422 como erros de interface legíveis e manter os identificadores técnicos somente como chave interna. Não duplicar regra de SLA, cursor, elegibilidade ou status no navegador.

- [ ] **Passo 4: Executar testes verdes e TypeScript.**

Executar: `npm run test --workspace=@wtg/web -- --run; npm run typecheck --workspace=@wtg/web`

Esperado: testes e verificação de tipos verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): tipa contratos operacionais do cliente`

### Task 10 — Reconstruir navegação e dashboard por perfil

**Arquivos:**
- Modificar: `apps/web/src/components/app-shell.tsx`.
- Modificar: `apps/web/src/app/dashboard/page.tsx`.
- Criar: `apps/web/src/components/admin-dashboard.tsx`.
- Criar: `apps/web/src/components/seller-dashboard.tsx`.
- Modificar: `apps/web/src/app/globals.css`.
- Criar: testes em `apps/web/src/components/*.test.tsx`.

- [ ] **Passo 1: Escrever testes de renderização vermelhos.**

Exigir admin com cartões de total, atribuições, posições, próximo vendedor e fila completa; seller com total próprio, comentários, SLA e apenas sua posição. Exigir que seller não tenha links de Fila global, Histórico global ou Usuários, nem nomes de colegas.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components`

Esperado: componentes específicos ainda inexistentes.

- [ ] **Passo 3: Implementar composição por papel.**

Montar o shell a partir do `role` retornado pela API; manter quatro páginas admin e visão própria do seller. Exibir situação e marcador sempre como texto/badge acessível. Remover `admin-controls.tsx` e qualquer referência a “Simular entrada de leads”.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components; npm run lint --workspace=@wtg/web`

Esperado: navegação e dashboard sem elementos indevidos por perfil.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): separa dashboards por perfil`

### Task 11 — Construir tabela de leads e modal de tratativa do vendedor

**Arquivos:**
- Criar: `apps/web/src/components/lead-table.tsx`.
- Criar: `apps/web/src/components/lead-treatment-modal.tsx`.
- Criar: `apps/web/src/lib/operations/treatment-actions.ts`.
- Modificar: `apps/web/src/app/dashboard/page.tsx`.
- Remover: `apps/web/src/components/comment-modal.tsx` depois da migração completa.
- Criar: `apps/web/src/components/lead-treatment-modal.test.tsx`.

- [ ] **Passo 1: Escrever testes vermelhos de interação.**

Cobrir coluna de responsável somente para admin, campos nome/empresa/campanha/telefone/e-mail/situação/marcador/prazo/comentários, botão `Registrar tratativa` somente para seller responsável, modal com três opções primárias, checkbox desqualificado e histórico somente leitura. Validar bloqueio de envio abaixo de 6 caracteres, exibição de erro 422 e incremento de contador após sucesso.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/lead-treatment-modal.test.tsx`

Esperado: falha porque o componente não existe.

- [ ] **Passo 3: Implementar tratamento real.**

Enviar `POST /api/leads/{id}/treatments`, mostrar progresso/sucesso/erro, invalidar a consulta do dashboard e renderizar histórico recebido da API. Administrador visualiza a mesma linha e histórico, sem botão ou campo editável. O comentário que marca desqualificação deve ser a submissão atual, nunca uma inferência da UI.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/lead-treatment-modal.test.tsx; npm run typecheck --workspace=@wtg/web`

Esperado: interação do vendedor e leitura administrativa verdes.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): permite tratativa de lead pelo vendedor`

### Task 12 — Construir gestão funcional de usuários

**Arquivos:**
- Modificar: `apps/web/src/app/usuarios/page.tsx`.
- Modificar: `apps/web/src/components/user-management.tsx`.
- Criar: `apps/web/src/components/user-form-modal.tsx`.
- Criar: `apps/web/src/components/user-password-modal.tsx`.
- Criar: `apps/web/src/lib/users/actions.ts`.
- Criar: `apps/web/src/components/user-management.test.tsx`.

- [ ] **Passo 1: Escrever testes vermelhos de controles reais.**

Cobrir botão `Novo usuário`, modal com nome/e-mail/papel/senha, senha obrigatória não vazia, criação bem-sucedida, `Pausar`/`Ativar` com confirmação, `Redefinir senha` com confirmação, estado de carregamento, feedback de sucesso/erro e ausência da senha após salvar.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/user-management.test.tsx`

Esperado: falha porque os controles atuais são apenas texto/botões desabilitados.

- [ ] **Passo 3: Implementar ações.**

Chamar as três rotas administrativas da Tarefa 6; usar botões HTML reais, modal com foco inicial, escape/cancelamento, confirmação antes da mutação e atualização da lista. Exibir status `Ativo`/`Pausado`; nunca mostrar `Bloqueado por atraso` como controle manual nem permitir pausar administrador caso a API não suporte esse fluxo.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/user-management.test.tsx; npm run lint --workspace=@wtg/web`

Esperado: todos os controles disparam ações tipadas e acessíveis.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): torna gestão de usuários operacional`

### Task 13 — Reconstruir fila, histórico e paginação administrativa

**Arquivos:**
- Modificar: `apps/web/src/app/fila/page.tsx`.
- Modificar: `apps/web/src/app/historico/page.tsx`.
- Modificar: `apps/web/src/components/pagination.tsx`.
- Criar: `apps/web/src/components/queue-table.tsx`.
- Criar: `apps/web/src/components/treatment-history-table.tsx`.
- Remover: `apps/web/src/components/resource-table.tsx` quando não houver consumidores.
- Criar: testes para tabelas e paginação.

- [ ] **Passo 1: Escrever testes vermelhos.**

Exigir fila admin ordenada a partir do cursor real, vendedor/nome, posição atual, disponibilidade e motivo; histórico com lead, vendedor, texto, situação, marcador e data; paginação com `<button>` anterior/próxima, `disabled` quando necessário e `aria-label` correspondente.

- [ ] **Passo 2: Executar testes vermelhos.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/queue-table.test.tsx src/components/treatment-history-table.test.tsx src/components/pagination.test.tsx`

Esperado: componentes e semântica novos ausentes.

- [ ] **Passo 3: Implementar visualização verdadeira.**

Usar somente projeções da Tarefa 7. A fila do admin exibe o cursor e a primeira pessoa elegível; indisponibilidades possuem badge e texto. O histórico não é a lista de assignments: deve ser `lead_treatments`. A paginação mantém query string, evita navegação quando desabilitada e não exibe rótulos colados como `AnteriorPágina`.

- [ ] **Passo 4: Executar testes verdes.**

Executar: `npm run test --workspace=@wtg/web -- --run src/components/queue-table.test.tsx src/components/treatment-history-table.test.tsx src/components/pagination.test.tsx`

Esperado: três telas administrativas com dados operacionais compreensíveis.

- [ ] **Passo 5: Versionar.**

Commit: `feat(gerec-leads): exibe fila e histórico operacionais`

### Task 14 — Consolidar CSS desktop, estados e acessibilidade

**Arquivos:**
- Modificar: `apps/web/src/app/globals.css`.
- Modificar: componentes criados nas Tarefas 10–13, somente para classes/atributos de acessibilidade.
- Criar: `apps/web/src/app/globals.test.ts` se a configuração permitir testar tokens; caso contrário validar exclusivamente por Playwright na Tarefa 15.

- [ ] **Passo 1: Definir os estados visuais verificáveis.**

Criar tokens para: indefinido vermelho, negociação amarelo, ganho verde, desqualificado cinza; todos com texto e contraste legível. Definir grid desktop, tabela com cabeçalho fixo de leitura, cards de fila, modal, estados de carregamento/erro/vazio e botão desabilitado.

- [ ] **Passo 2: Implementar sem inventar dados.**

Remover colunas técnicas como conteúdo principal, exibir `Não informado` para empresa/campanha ausentes, usar a formatação de telefone da Tarefa 9 e manter largura mínima de 1280 px. Não inserir gradientes, elementos decorativos sem função ou controles falsos.

- [ ] **Passo 3: Verificar qualidade estática.**

Executar: `npm run lint --workspace=@wtg/web; npm run typecheck --workspace=@wtg/web; npm run build --workspace=@wtg/web`

Esperado: lint, tipos e build verdes.

- [ ] **Passo 4: Versionar.**

Commit: `style(gerec-leads): consolida interface operacional desktop`

### Task 15 — Cobrir fluxos reais com E2E e validação visual

**Arquivos:**
- Modificar: `tests/e2e/auth.spec.ts`.
- Modificar: `tests/e2e/roles.spec.ts`.
- Modificar: `tests/e2e/lead-lifecycle.spec.ts`.
- Criar: `tests/e2e/admin-operations.spec.ts`.
- Criar: `tests/e2e/seller-treatment.spec.ts`.
- Criar: `tests/e2e/visual/` com snapshots aprovados.
- Modificar: `playwright.config.ts` somente se necessário para estabilidade de dados/servidores.

- [ ] **Passo 1: Preparar fixtures determinísticas.**

Usar relógio controlável e dados sintéticos: seis contas, seis leads distribuídos Renato 2/Sandra 2/Jessica 1/Nelma 1, cursor seguinte Jessica, ao menos um prazo vencido e um lead desqualificado. Não usar credenciais de produção nem Google Sheets real.

- [ ] **Passo 2: Escrever E2E vermelhos pela interface.**

Cobrir admin cria seller e vê-o no fim da fila, pausa/ativa seller e redefine senha; admin lê mas não encontra botão de editar tratativa; seller abre modal, comentário curto falha, negociação salva, contador sobe e status aparece; desqualificação com comentário encerra SLA; seller não vê colegas; anterior/próxima são botões corretos; fila mostra Jessica como próxima após a distribuição descrita.

- [ ] **Passo 3: Executar E2E vermelho.**

Executar: `npx playwright test tests/e2e/admin-operations.spec.ts tests/e2e/seller-treatment.spec.ts --project=chromium`

Esperado: falhas até a aplicação completa estar conectada à API fixture.

- [ ] **Passo 4: Criar capturas de referência.**

Adicionar `expect(page).toHaveScreenshot(...)` a 1440 × 900 para dashboard admin, usuários/modal, fila/histórico, dashboard seller e modal de tratativa. Mascarar relógio variável; não mascarar status, nomes, contadores, botões ou dados visíveis.

- [ ] **Passo 5: Executar E2E verde.**

Executar: `npx playwright test --project=chromium`

Esperado: todos os fluxos e screenshots verdes, sem chamadas diretas à API para a ação que a interface deve realizar.

- [ ] **Passo 6: Versionar.**

Commit: `test(gerec-leads): valida operação administrativa e vendedor`

### Task 16 — Executar o gate final e registrar evidências

**Arquivos:**
- Criar: `docs/evidencias/2026-08-28-reconstrucao-operacional.md`.
- Modificar: `ROADMAP.md` apenas para registrar o estado real das entregas concluídas.
- Gerar: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`.

- [ ] **Passo 1: Executar todas as verificações.**

Executar, nesta ordem:

```powershell
python -m pytest apps/api/tests -q
npm run test --workspace=@wtg/web -- --run
npm run lint --workspace=@wtg/web
npm run typecheck --workspace=@wtg/web
npm run build --workspace=@wtg/web
node --test tests/contracts/*.test.mjs
npx playwright test --project=chromium
powershell -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1
git diff --check
```

- [ ] **Passo 2: Registrar evidências factuais.**

Informar versões/comandos, contagem de testes, resultado de cada gate, capturas produzidas, limitações conhecidas e confirmação de que não foram incluídos `.env` ou arquivos locais alheios.

- [ ] **Passo 3: Revisão independente.**

Enviar o diff completo para um subagente revisor. Resolver qualquer achado crítico e repetir os comandos afetados.

- [ ] **Passo 4: Versionar.**

Commit: `docs(gerec-leads): registra evidências da reconstrução`

## Revisão do plano

### Cobertura do desenho aprovado

| Decisão/critério | Tarefas |
| --- | --- |
| Governança e divergências do SPEC | 1 |
| SLA 09–18 e lembrete | 2, 3, 4, 5 |
| Tratativa/status/marcador/comentários | 3, 4, 7, 8, 11, 15 |
| Bloqueio automático e pausa manual | 3, 5, 6, 7, 13, 15 |
| Usuários, senha e sessões | 6, 12, 15 |
| Cursor e ordem dinâmica | 5, 7, 10, 13, 15 |
| Projeções e permissões admin/vendedor | 7, 8, 10, 11, 15 |
| Interface sem controles falsos | 10–14 |
| Paginação real | 13, 15 |
| E2E, visual, build e evidência | 15, 16 |

### Resultado da auto-revisão

- Não há passo que dependa de regra não aprovada: os pontos que contradizem o SPEC são formalizados na Tarefa 1 antes da implementação.
- Todas as alterações de domínio começam por teste vermelho e terminam em teste verde.
- A UI não inicia antes de contratos e projeções de API estáveis.
- O fornecedor de e-mail, planilha definitiva, recorrência/transferência/créditos e suporte mobile permanecem explicitamente fora deste corte.
