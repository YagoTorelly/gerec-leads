# Cadastro manual, fila alternativa e exportações — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que administradores cadastrem leads manuais em uma fila alternativa independente, que vendedores recebam/tratem esses leads e que administradores exportem todos os leads em Excel com histórico de exportações separado.

**Architecture:** O backend criará um comando transacional para lead manual e reutilizará o motor FIFO com `queueKind=manual`, mantendo cursor e auditoria separados de `queueKind=automatic`. A web consumirá rotas administrativas para cadastro, exportação e histórico; a geração do `.xlsx` permanecerá no backend. Os dois gráficos de relatórios serão convertidos em colunas verticais, um por linha completa.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, MongoDB/Motor, pytest; Next.js 16, React 19, TypeScript, Vitest, Playwright, `openpyxl` para Excel.

**Spec:** `docs/superpowers/specs/2026-09-22-cadastro-manual-fila-alternativa-exportacoes-design.md`

## Global Constraints

- Somente administradores podem criar leads manuais, exportar leads e consultar o histórico de exportações.
- O vendedor não escolhe o responsável; a fila alternativa usa a mesma ordem da fila principal e um cursor independente.
- Vendedores Pausados ou indisponíveis são pulados; o próximo vendedor Ativo elegível recebe o lead.
- A fila alternativa não altera cursor, posição, créditos ou atribuições da fila automática.
- Situação inicial de todo lead manual: `Indefinido`.
- Todo lead manual recebe `manualQueueLeadId` único, gerado pelo backend; não reutiliza `sourceLeadId`.
- Leads manuais atribuídos geram a notificação interna já existente; não criar envio de e-mail.
- O download é exclusivamente um arquivo Excel `.xlsx` contendo leads; tratativas e histórico de exportações não são baixados.
- Datas exportadas usam `America/Sao_Paulo`; telefones e identificadores são células de texto.
- O histórico de exportações mostra data/hora, administrador responsável, quantidade, filtros e status.
- O frontend nunca é fonte de autorização; comandos críticos e escopo vivem na API/domínio.
- Toda alteração de banco usa migração versionada; não editar migrações aplicadas.
- Testes de concorrência, idempotência, rollback, escopo e falha de exportação são obrigatórios.
- Preservar os arquivos preexistentes `D apps/api/.env.example` e `?? tools/google-sheets-diagnostic/`.

## Mapa de arquivos e interfaces

### Backend

- `apps/api/src/gerec_api/domain/manual_leads.py`: comando e tipos do cadastro manual.
- `apps/api/src/gerec_api/domain/queue.py`: seleção com `queueKind` e cursor alternativo.
- `apps/api/src/gerec_api/domain/exportations.py`: contrato e geração de exportação.
- `apps/api/src/gerec_api/routes/admin.py`: rotas administrativas de criação, exportação e histórico.
- `apps/api/src/gerec_api/auth/permissions.py`: leituras administrativas e escopo.
- `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`: persistência do lead manual.
- `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`: estado/cursor por tipo de fila.
- `apps/api/src/gerec_api/infrastructure/mongo/exportation_repository.py`: histórico de exportações.
- `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260922_manual_queue_exportations.py`: migração versionada.
- `apps/api/tests/integration/test_manual_leads.py`: comandos, autorização, fila e notificações.
- `apps/api/tests/integration/test_exportations.py`: Excel, histórico e falhas.

### Web

- `apps/web/src/app/usuarios/page.tsx` ou shell administrativo: ação “Adicionar leads”.
- `apps/web/src/components/manual-lead-form.tsx`: formulário administrativo.
- `apps/web/src/components/exportations-panel.tsx`: download e histórico.
- `apps/web/src/lib/admin/manual-lead-actions.ts`: Server Action de criação.
- `apps/web/src/lib/admin/exportation-queries.ts`: consulta do histórico.
- `apps/web/src/app/exportacoes/download/route.ts`: Route Handler autenticado que transmite o `.xlsx`.
- `apps/web/src/lib/api/types.ts` e `client.ts`: contratos HTTP.
- `apps/web/src/app/relatorios/page.tsx`, `reports-dashboard.tsx`, `globals.css`: colunas em linhas completas.
- Testes DOM/unitários correspondentes em `apps/web/src/components/*test.tsx` e `apps/web/src/lib/admin/*test.ts`.

## Task 1: Modelo de dados, ID manual e cursor alternativo

**Files:**
- Create: `apps/api/src/gerec_api/domain/manual_leads.py`
- Modify: `apps/api/src/gerec_api/domain/queue.py`
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/lead_repository.py`
- Modify: `apps/api/src/gerec_api/infrastructure/mongo/queue_repository.py`
- Create: `apps/api/src/gerec_api/infrastructure/mongo/migrations/20260922_manual_queue_exportations.py`
- Test: `apps/api/tests/integration/test_manual_leads.py`

**Interfaces:**
- Produces `ManualLeadCommand(name, email, phone, campaign?, source?, idempotency_key)`.
- Produces `create_manual_lead(actor, command, now) -> ManualLeadResult`.
- Produces `select_next_seller(queue_kind: Literal["automatic", "manual"], now) -> SellerSelection`.
- `manualQueueLeadId` é texto `MAN-` + UUID4, com índice único.

- [ ] Escrever testes vermelhos para criação, situação inicial, ID único, cursor independente, salto de Pausado, herança de campanha e idempotência.
- [ ] Rodar `python -m pytest apps/api/tests/integration/test_manual_leads.py -q`; confirmar falhas por interfaces ausentes.
- [ ] Implementar o comando transacional e migração sem alterar o cursor automático.
- [ ] Rodar o teste focado e a suíte de filas; confirmar verde.
- [ ] Commit: `feat(api): adiciona fila alternativa para leads manuais`.

## Task 2: Rotas administrativas de criação e notificação

**Files:**
- Modify: `apps/api/src/gerec_api/routes/admin.py`
- Modify: `apps/api/src/gerec_api/main.py`
- Modify: `apps/api/src/gerec_api/domain/lead_notifications.py`
- Test: `apps/api/tests/integration/test_manual_leads.py`

**Interfaces:**
- `POST /api/admin/leads/manual` recebe nome, e-mail, telefone, campanha/origem opcional e `Idempotency-Key`.
- Retorna `201` com `leadId`, `manualQueueLeadId`, `assigneeId`, `assignedAt`, `commercialStatus="undefined"` e `source="manual"`.
- Vendedor recebe `403` em criação; campos inválidos retornam `422`.
- A atribuição publica a mesma sequência/cursor de notificação já consumida pelo dashboard.

- [ ] Escrever testes vermelhos de autorização, validação, resposta, notificação e rollback.
- [ ] Rodar testes e confirmar falhas esperadas.
- [ ] Implementar rota fina, delegando ao comando transacional.
- [ ] Rodar integração focada e permissões; confirmar verde.
- [ ] Commit: `feat(api): expõe cadastro manual de leads`.

## Task 3: Exportação Excel e histórico administrativo

**Files:**
- Create: `apps/api/src/gerec_api/domain/exportations.py`
- Create: `apps/api/src/gerec_api/infrastructure/mongo/exportation_repository.py`
- Modify: `apps/api/src/gerec_api/routes/admin.py`
- Modify: `apps/api/src/gerec_api/main.py`
- Test: `apps/api/tests/integration/test_exportations.py`

**Interfaces:**
- `GET /api/admin/exportations` retorna histórico paginado com `createdAt`, `administratorName`, `leadCount`, `filters` e `status`.
- `GET /api/admin/exportations/leads` retorna `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` e cria registro de sucesso/erro.
- `ExportationService.export_leads(actor, filters, now) -> ExportationResult`.
- Datas no workbook são formatadas em `America/Sao_Paulo`; IDs/telefones são texto.

- [ ] Escrever testes vermelhos para Excel com cabeçalhos, exportação vazia, histórico, vendedor proibido e falha sem falso sucesso.
- [ ] Rodar testes focados e confirmar falhas esperadas.
- [ ] Implementar geração com `openpyxl`, auditoria de status e tratamento seguro de erro.
- [ ] Rodar testes de exportação e validar MIME, colunas, timezone e conteúdo.
- [ ] Commit: `feat(api): adiciona exportação administrativa de leads`.

## Task 4: Formulário web de lead manual

**Files:**
- Create: `apps/web/src/components/manual-lead-form.tsx`
- Create: `apps/web/src/lib/admin/manual-lead-actions.ts`
- Modify: `apps/web/src/lib/api/types.ts`
- Modify: `apps/web/src/lib/api/client.ts`
- Modify: `apps/web/src/app/usuarios/page.tsx`
- Test: `apps/web/src/components/manual-lead-form.test.tsx`
- Test: `apps/web/src/lib/admin/manual-lead-actions.test.ts`

**Interfaces:**
- `ManualLeadForm` aceita `latestCampaignDefaults` e não renderiza seletor de responsável.
- Server Action `createManualLeadAction(input) -> { ok: boolean; message: string; lead? }`.
- Campos name/email/phone obrigatórios; status é exibido como `Indefinido` e não editável.

- [ ] Escrever testes vermelhos para campos, status fixo, ausência de responsável, sucesso, erro e seller sem acesso.
- [ ] Rodar Vitest focado e confirmar falhas esperadas.
- [ ] Implementar modal/painel e Server Action com revalidação de dashboard/fila/notificações.
- [ ] Rodar Vitest, typecheck e lint.
- [ ] Commit: `feat(web): adiciona cadastro manual de leads`.

## Task 5: Guia de exportações e histórico

**Files:**
- Create: `apps/web/src/components/exportations-panel.tsx`
- Create: `apps/web/src/lib/admin/exportation-queries.ts`
- Create: `apps/web/src/app/exportacoes/download/route.ts`
- Modify: `apps/web/src/components/app-shell.tsx`
- Modify: `apps/web/src/lib/api/types.ts`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/components/exportations-panel.test.tsx`
- Test: `apps/web/src/lib/admin/exportation-queries.test.ts`
- Test: `apps/web/src/components/app-shell.test.tsx`

**Interfaces:**
- Rota `/exportacoes` somente para administrador.
- `getExportationHistory()` chama `GET /api/admin/exportations`.
- `GET /exportacoes/download` no Route Handler web repassa a autenticação e transmite o `.xlsx` sem converter bytes em string ou expor credenciais.
- A tela mostra data/hora, administrador responsável, quantidade, filtros e status; não mostra botão para baixar histórico.

- [ ] Escrever testes vermelhos de navegação admin/seller, download apenas de leads, histórico, loading, erro e retry.
- [ ] Rodar Vitest focado e confirmar falhas esperadas.
- [ ] Implementar guia e integração no shell mantendo o shell em erro.
- [ ] Rodar Vitest, typecheck e lint.
- [ ] Commit: `feat(web): adiciona guia de exportações`.

## Task 6: Layout dos relatórios em colunas

**Files:**
- Modify: `apps/web/src/components/reports-dashboard.tsx`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/components/reports-dashboard.test.tsx`

**Interfaces:**
- Mantém somente os grupos `bySituation` e `bySeller` já existentes.
- Cada grupo renderiza colunas verticais em um container de largura total.
- Cada coluna possui texto acessível `Nome: N` e altura proporcional ao maior valor do próprio grupo.

- [ ] Escrever teste vermelho que exija dois containers em linhas distintas, classes de coluna e texto equivalente.
- [ ] Rodar o teste e confirmar falha com o layout atual.
- [ ] Implementar CSS/markup sem dependência de biblioteca de gráficos.
- [ ] Rodar testes, typecheck, lint e screenshot local 1440x900.
- [ ] Commit: `feat(web): reorganiza relatórios em colunas`.

## Task 7: E2E, evidências e contexto mestre

**Files:**
- Create or Modify: `apps/web/e2e/cadastro-manual-exportacoes.spec.ts`
- Create: `docs/evidencias/2026-09-22-cadastro-manual-fila-alternativa-exportacoes.md`
- Modify: `docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md` only through generator
- Modify: `.github/workflows/gerec-leads-ci.yml` only if the existing contract tests require the new route/build gate

**Interfaces:**
- E2E admin cria lead manual, confirma ID/Indefinido, aguarda notificação do vendedor e verifica tratativa.
- E2E admin baixa `.xlsx`, valida nome/MIME/colunas e confere uma linha no arquivo.
- E2E admin consulta histórico; seller não vê `/exportacoes` nem acessa endpoints.
- E2E confirma fila automática sem alteração e relatórios com duas linhas completas de colunas.

- [ ] Escrever os fluxos E2E antes da implementação final da integração.
- [ ] Rodar `npm run test:e2e -- cadastro-manual-exportacoes.spec.ts` e corrigir somente fixture/selector/contrato legítimo.
- [ ] Capturar telas 1440x900 de cadastro, exportação e relatórios.
- [ ] Rodar gates: `python -m pytest apps/api/tests -q`, `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:e2e`, `git diff --check`.
- [ ] Registrar totais, screenshots, permissões e limitações reais na evidência.
- [ ] Regenerar contexto com `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1`.
- [ ] Commit: `test: valida cadastro manual e exportações`.

## Execution order and review gates

Tasks 1–3 são backend e devem ser revisadas antes de Tasks 4–5. Task 6 pode
rodar em paralelo com Task 4–5 porque usa apenas o contrato já existente de
relatórios. Task 7 só começa após todas as integrações anteriores.

Cada task exige implementador separado, pacote de revisão, revisor independente,
correção e re-revisão até não haver findings críticos/importantes. Nenhuma task
é marcada como concluída sem testes recentes e registro no ledger SDD.
