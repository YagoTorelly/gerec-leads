# Alertas de novos leads por e-mail — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar alertas SMTP seguros e idempotentes para novos leads agrupados por vendedor/sincronização, avisos individuais de transferência e horários corretos em `America/Sao_Paulo`.

**Architecture:** A atribuição continua transacional no MongoDB. Eventos leves entram na `notification_outbox`; um agregador forma um grupo por `syncRunId + sellerId`, enquanto transferências usam evento individual. O worker Railway resolve os dados mínimos, renderiza texto/HTML e entrega por SMTP STARTTLS com retry/dead-letter.

**Tech Stack:** Python 3, FastAPI, MongoDB/PyMongo, `smtplib`/MIME da biblioteca padrão, Railway worker, Next.js/React, Vitest, Pytest, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-03-alertas-email-leads-design.md`

## Global Constraints

- Ler integralmente `AGENTS.md`, `SPEC_GERENCIADOR_DE_LEADS_WTG.md` e `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` antes de cada tarefa.
- MongoDB é a única persistência; não adicionar Supabase/PostgreSQL/n8n.
- Regras críticas permanecem em serviços/comandos Python, nunca em React, controller ou worker de integração.
- Google Sheets é somente origem; nunca escrever na planilha.
- SMTP: `smtp.oncorretor.com.br:587`, STARTTLS obrigatório, remetente `contato@wtgseguros.com.br`.
- `SMTP_PASSWORD` e demais segredos só existem nas variáveis da Railway.
- Nenhum e-mail de lead inclui campanha, e-mail do lead ou identificadores internos.
- Datas sem fuso da origem são `America/Sao_Paulo`; armazenamento é UTC; apresentação é São Paulo.
- Uma falha de e-mail nunca desfaz atribuição, transferência, SLA ou fila.
- Aplicar TDD: teste vermelho observado antes de cada implementação.
- Não alterar `D apps/api/.env.example` nem `?? tools/google-sheets-diagnostic/`.
- Não fazer push/deploy sem autorização explícita para a etapa; commits devem ser pequenos e auditáveis.

## Mapa de arquivos e responsabilidades

- `apps/api/src/gerec_api/domain/normalization.py`: interpretação de datas da origem.
- `apps/api/src/gerec_api/automation/sync_job.py`: ciclo de sincronização e `syncRunId`.
- `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`: eventos transacionais de atribuição/transferência.
- `apps/api/src/gerec_api/infrastructure/mongo/collections.py` e `indexes.py`: nomes e índices da outbox.
- `apps/api/src/gerec_api/automation/outbox_worker.py`: claim, agrupamento e entrega.
- `apps/api/src/gerec_api/automation/email_templates.py`: MIME/texto/HTML sem regra de negócio.
- `apps/api/src/gerec_api/automation/smtp_delivery.py`: adapter SMTP isolado e testável.
- `apps/api/src/gerec_api/config.py`: configuração validada sem segredos no cliente.
- `apps/api/src/gerec_api/routes/admin.py`: endpoint administrativo de leitura da outbox.
- `apps/api/src/gerec_api/auth/permissions.py`: leitura administrativa segura de estado da outbox.
- `apps/api/tests/unit/` e `apps/api/tests/integration/`: testes de domínio, Mongo e concorrência.
- `apps/web/src/lib/dashboard/format.ts`: apresentação de timestamps em São Paulo.
- `apps/web/src/components/admin-notification-status.tsx`: estados visuais de alertas administrativos.
- `docs/DECISOES.md`, `SPEC_GERENCIADOR_DE_LEADS_WTG.md`, `docs/ARQUITETURA.md`: governança e contratos.
- `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md`: contexto regenerado após mudanças documentais.

---

### Task 1: Registrar governança e contrato operacional

**Files:**
- Modify: `SPEC_GERENCIADOR_DE_LEADS_WTG.md` seção 39 e dependências de implantação.
- Modify: `docs/DECISOES.md` adicionando decisão após DEC-029.
- Modify: `docs/ARQUITETURA.md` fronteira do outbox worker.
- Regenerate: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` via `scripts/generate-master-context.ps1`.
- Test: inspeção documental com `rg`.

**Interfaces:** produz os nomes de eventos, variáveis e política temporal consumidos pelas tarefas seguintes.

- [ ] **Step 1: Escrever primeiro a verificação documental**

```powershell
rg -n "assignment_email_requested|owner_transfer_email_requested|SMTP_HOST|America/Sao_Paulo|agrup" SPEC_GERENCIADOR_DE_LEADS_WTG.md docs/DECISOES.md docs/ARQUITETURA.md
```

Esperado: falha porque os contratos novos ainda não estão registrados.

- [ ] **Step 2: Registrar regra anterior, nova regra, motivo, impacto, migração, testes e aprovação de Yago** nas três documentações canônicas.
- [ ] **Step 3: Regenerar o contexto mestre** com `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`.
- [ ] **Step 4: Reexecutar o `rg` e confirmar todos os contratos.**
- [ ] **Step 5: Commit** `docs: registra alertas smtp e contrato de horario`.

### Task 2: Corrigir e congelar o contrato de horário

**Files:**
- Modify: `apps/api/src/gerec_api/domain/normalization.py` apenas se a regressão localizar parser incorreto.
- Modify: `apps/web/src/lib/dashboard/format.ts` apenas se a regressão localizar formato incorreto.
- Test: `apps/api/tests/unit/test_normalization.py` e novo teste de formato web.

**Interfaces:** `normalize_datetime(value) -> datetime | None` interpreta valor ingênuo em São Paulo e retorna UTC; `formatDateTime(value) -> string` exibe São Paulo.

- [ ] **Step 1: Adicionar testes vermelhos** para `14:11` ingênuo, `17:11Z`, offset externo e timestamp inválido.
- [ ] **Step 2: Executar** `python -m pytest apps/api/tests/unit/test_normalization.py -q` e `npm test -- --run src/lib/dashboard/format.test.ts`; confirmar falha da expectativa nova.
- [ ] **Step 3: Implementar somente a normalização/formatação mínima**, sem deslocar timestamps já aware.
- [ ] **Step 4: Executar os testes direcionados e depois a suíte completa de API/Web.**
- [ ] **Step 5: Auditar registros reais/legados por consulta somente leitura; nenhuma migração corretiva sem classificação explícita.**
- [ ] **Step 6: Commit** `fix: normaliza timestamps da origem em sao paulo`.

### Task 3: Propagar `syncRunId` até a atribuição

**Files:**
- Modify: `apps/api/src/gerec_api/automation/sync_job.py`.
- Modify: `apps/api/src/gerec_api/domain/queue.py` assinaturas do comando.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py` payload do evento de atribuição.
- Test: `apps/api/tests/unit/test_sync_job.py` e `apps/api/tests/integration/test_queue_transactions.py`.

**Interfaces:** `QueueService.distribute_ready(lead_id, command_id, *, actor_id, sync_run_id: str | None = None) -> AssignmentResult`; eventos carregam `syncRunId` quando atribuídos pelo `SyncJob`.

- [ ] **Step 1: Criar teste vermelho** que execute uma sincronização e inspecione o evento criado para conter o mesmo `syncRunId`.
- [ ] **Step 2: Rodar o teste direcionado e confirmar falha por ausência do campo.**
- [ ] **Step 3: Propagar o argumento sem mudar cursor, critérios de elegibilidade ou créditos.**
- [ ] **Step 4: Rodar testes de sincronização, fila e concorrência.**
- [ ] **Step 5: Commit** `feat: vincula atribuicoes ao ciclo de sincronizacao`.

### Task 4: Criar eventos de notificação de atribuição e transferência

**Files:**
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py` se uma chave auxiliar exigir índice.
- Test: `apps/api/tests/integration/test_queue_transactions.py`.

**Interfaces:** `lead.assignment_email_requested` usa `groupKey=assignment-summary:{syncRunId}:{sellerId}`; `lead.owner_transfer_email_requested` usa `owner-transfer:{leadId}:{commandId}`.

- [ ] **Step 1: Escrever testes vermelhos** para resumo automático e transferência individual, verificando destinatário lógico, lead ID e ausência de dados pessoais redundantes.
- [ ] **Step 2: Executar os testes e confirmar falha.**
- [ ] **Step 3: Gravar eventos na mesma transação da atribuição/transferência; manter o evento SLA existente separado.**
- [ ] **Step 4: Verificar replay idempotente e cursor inalterado.**
- [ ] **Step 5: Commit** `feat: grava eventos de alerta de atribuicao`.

### Task 5: Implementar agregação por vendedor e sincronização

**Files:**
- Modify: `apps/api/src/gerec_api/automation/outbox_worker.py` ou criar `apps/api/src/gerec_api/automation/notification_groups.py`.
- Test: `apps/api/tests/unit/test_notification_groups.py` e `apps/api/tests/integration/test_automation_idempotency.py`.

**Interfaces:** `NotificationGroupRepository.claim_group(group_key, now, max_attempts) -> NotificationGroup`; `NotificationGroupRepository.mark_group_sent(group, now) -> bool`; grupos de transferência nunca agregam com sincronização.

- [ ] **Step 1: Criar testes vermelhos** para dois leads do mesmo vendedor, dois vendedores da mesma sincronização, grupo vazio e dois workers concorrentes.
- [ ] **Step 2: Confirmar falhas com `pytest`.**
- [ ] **Step 3: Implementar claim atômico por `groupKey`, lock e fencing token reaproveitando a outbox.**
- [ ] **Step 4: Marcar todos os eventos do grupo somente após entrega bem-sucedida.**
- [ ] **Step 5: Testar crash antes/depois do envio e documentar limite de duplicidade externa.**
- [ ] **Step 6: Commit** `feat: agrupa alertas por sincronizacao e vendedor`.

### Task 6: Criar templates de e-mail HTML e texto

**Files:**
- Create: `apps/api/src/gerec_api/automation/email_templates.py`.
- Test: `apps/api/tests/unit/test_email_templates.py`.

**Interfaces:** `render_assignment_summary(items, dashboard_url) -> EmailMessageData`; `render_owner_transfer(item, dashboard_url) -> EmailMessageData`.

- [ ] **Step 1: Escrever testes vermelhos** para assunto, texto aprovado, nome, telefone, link e ausência de campanha/e-mail/IDs.
- [ ] **Step 2: Rodar `pytest apps/api/tests/unit/test_email_templates.py -q` e confirmar falha.**
- [ ] **Step 3: Implementar MIME multipart com versão texto simples e HTML escapado.**
- [ ] **Step 4: Testar nomes/telefones com caracteres especiais e lista vazia.**
- [ ] **Step 5: Commit** `feat: adiciona templates de alerta por email`.

### Task 7: Implementar adapter SMTP STARTTLS

**Files:**
- Create: `apps/api/src/gerec_api/automation/smtp_delivery.py`.
- Modify: `apps/api/src/gerec_api/config.py` para configuração validada.
- Test: `apps/api/tests/unit/test_smtp_delivery.py`.

**Interfaces:** `SmtpSettings.from_env() -> SmtpSettings`; `SmtpDelivery(settings, smtp_factory=smtplib.SMTP).send(message, idempotency_key) -> None`.

- [ ] **Step 1: Escrever testes vermelhos** para host/porta, STARTTLS, login, remetente, timeout e falhas convertidas em erro retryable.
- [ ] **Step 2: Confirmar falha dos testes.**
- [ ] **Step 3: Implementar com `smtplib.SMTP`, `starttls()`, `login()` e fechamento garantido.**
- [ ] **Step 4: Garantir que senha nunca apareça em exceção/log.**
- [ ] **Step 5: Rodar testes unitários e lint Python.**
- [ ] **Step 6: Commit** `feat: entrega alertas via smtp starttls`.

### Task 8: Integrar worker, dados mínimos e retry

**Files:**
- Modify: `apps/api/src/gerec_api/automation/outbox_worker.py`.
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/indexes.py` para consultas por IDs/grupos.
- Test: `apps/api/tests/integration/test_automation_idempotency.py` e novo teste de integração de entrega.

**Interfaces:** `EmailNotificationWorker.process(batch_size, now=None) -> int`; resolução de vendedor/lead retorna somente e-mail do vendedor, nome e telefone do lead.

- [ ] **Step 1: Escrever testes vermelhos** de envio agrupado, transferência individual, retry, dead-letter e vendedor sem e-mail.
- [ ] **Step 2: Confirmar falhas.**
- [ ] **Step 3: Integrar agregador, templates e SMTP no worker Railway sem remover o webhook até a substituição estar coberta.**
- [ ] **Step 4: Executar entrega somente depois do claim; `mark_sent` só após sucesso.**
- [ ] **Step 5: Verificar que falha não altera leads, assignments, queue_state ou SLA.**
- [ ] **Step 6: Commit** `feat: integra worker de alertas de leads`.

### Task 9: Configurar Railway e documentação operacional

**Files:**
- Modify: `docs/ARQUITETURA.md` seção de configuração e operação Railway, sem valores secretos.
- Test: validação de configuração unitária e inspeção de arquivos.

**Interfaces:** variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, `DASHBOARD_PUBLIC_URL`, `SMTP_ENABLED`.

- [ ] **Step 1: Escrever teste vermelho** que rejeite configuração SMTP incompleta quando `SMTP_ENABLED=true`.
- [ ] **Step 2: Implementar validação; permitir `SMTP_ENABLED=false` em desenvolvimento sem enviar mensagens.**
- [ ] **Step 3: Documentar configuração Railway e procedimento de rotação da senha.**
- [ ] **Step 4: Confirmar que nenhum segredo está no repositório com `rg`.**
- [ ] **Step 5: Commit** `chore: documenta configuracao smtp da railway`.

### Task 10: Expor observabilidade administrativa sem dados sensíveis

**Files:**
- Modify: `apps/api/src/gerec_api/auth/permissions.py`.
- Modify: `apps/api/src/gerec_api/routes/admin.py`.
- Create: `apps/web/src/components/admin-notification-status.tsx`.
- Modify: `apps/web/src/components/admin-dashboard.tsx` para incluir o painel de status.
- Test: API/Web de leitura administrativa.

**Interfaces:** leitura admin-only de contagens/status: pending, processing, retry, sent, dead_letter, último erro truncado e última sincronização; nenhuma ação de edição de tratativa.

- [ ] **Step 1: Escrever testes vermelhos** para admin autorizado, vendedor negado e ausência de senha/payload pessoal.
- [ ] **Step 2: Implementar projeção agregada server-side com paginação/limites.**
- [ ] **Step 3: Renderizar estados claros de pendente, retry e dead-letter.**
- [ ] **Step 4: Rodar API/Web tests e verificar acessibilidade básica.**
- [ ] **Step 5: Commit** `feat: adiciona observabilidade dos alertas`.

### Task 11: E2E e screenshots do fluxo completo

**Files:**
- Modify/Create: `tests/e2e/email-alerts.spec.ts` e fixtures de teste.
- Create: evidências em diretório de artefatos do teste, sem dados reais.

**Interfaces:** sincronização mock → atribuição → resumo; transferência → aviso individual; relógio controlado; SMTP fake.

- [ ] **Step 1: Escrever cenários E2E vermelhos** para resumo agrupado, transferência, falha/retry e horário 14:11.
- [ ] **Step 2: Executar Playwright em viewport 1440×900 e confirmar falhas antes da implementação final.**
- [ ] **Step 3: Implementar fixtures/fakes isolados sem SMTP real.**
- [ ] **Step 4: Capturar screenshots de dashboard admin, dashboard vendedor, outbox e lead com horário correto.**
- [ ] **Step 5: Commit** `test: cobre alertas de leads no fluxo e2e`.

### Task 12: Verificação final, piloto e handoff

**Files:**
- Create/Modify: `.superpowers/sdd/2026-09-03-alertas-email-leads/progress.md`, sem apagar histórico.
- Review: diff completo, SPEC, design e plano.

- [ ] **Step 1: Rodar API completa:** `python -m pytest apps/api/tests -q`.
- [ ] **Step 2: Rodar Web completa:** `npm test` em `apps/web`.
- [ ] **Step 3: Rodar `npm run typecheck`, `npm run lint` e `npm run build`.**
- [ ] **Step 4: Rodar E2E/screenshot e revisar manualmente as evidências.**
- [ ] **Step 5: Verificar `git diff --check`, arquivos protegidos e ausência de segredos.**
- [ ] **Step 6: Atualizar contexto mestre após todas as mudanças documentais.**
- [ ] **Step 7: Solicitar revisão independente; corrigir achados; só então preparar rollout/piloto com `SMTP_ENABLED=false` inicialmente e habilitação autorizada.**
- [ ] **Step 8: Commit final de documentação/evidências; não declarar concluído sem saídas recentes dos comandos.**

## Critério de conclusão

O trabalho só está concluído quando os critérios de aceite da especificação de design forem demonstrados por testes recentes, revisão independente, screenshots em 1440×900, configuração SMTP validada em staging e evidência de que atribuições/fila permanecem corretas quando o provedor de e-mail falha.

## Matriz de cobertura do design

| Design | Tarefas do plano |
|---|---|
| Arquitetura e fluxo de sincronização | 3, 4, 5, 8 |
| Transferência individual | 4, 5, 8, 11 |
| Contrato de eventos e idempotência | 3, 4, 5, 8 |
| Templates HTML/texto | 6 |
| SMTP STARTTLS e configuração | 7, 9 |
| Retry, dead-letter e observabilidade | 5, 8, 10, 12 |
| Timezone e registros legados | 1, 2, 12 |
| Segurança, permissões e dados mínimos | 1, 6, 8, 10, 11 |
| E2E, screenshots, rollout e rollback | 9, 11, 12 |
