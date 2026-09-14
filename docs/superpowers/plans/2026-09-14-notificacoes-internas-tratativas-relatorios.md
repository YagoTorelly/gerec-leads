# NotificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas, tratativas e relatÃƒÆ’Ã‚Â³rios Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna de novos leads, situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o Potencial, marcador Desqualificado reversÃƒÆ’Ã‚Â­vel, destaque de leads sem tratativa, filtros/ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e relatÃƒÆ’Ã‚Â³rios administrativos seguros.

**Architecture:** A API Python mantÃƒÆ’Ã‚Â©m regras, autorizaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e projeÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes de leitura. Um cursor persistente no usuÃƒÆ’Ã‚Â¡rio delimita a janela de novos leads sem alterar FIFO; o frontend Next.js apenas consome contratos autorizados. RelatÃƒÆ’Ã‚Â³rios sÃƒÆ’Ã‚Â£o agregaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes MongoDB exclusivas de administrador e usam a atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o do proprietÃƒÆ’Ã‚Â¡rio atual.

**Tech Stack:** Python 3.13, FastAPI, Pydantic, PyMongo/MongoDB replica set, pytest; Next.js 16, React 19, TypeScript, Vitest, Testing Library e agent-browser.

**Spec:** docs/superpowers/specs/2026-09-14-notificacoes-internas-tratativas-relatorios-design.md

## Global Constraints

- Trabalhar no worktree feat/migracao-mongodb-vercel-railway; nÃƒÆ’Ã‚Â£o modificar apps/api/.env.example removido ou tools/google-sheets-diagnostic/ nÃƒÆ’Ã‚Â£o rastreado.
- NÃƒÆ’Ã‚Â£o criar e-mail, SMTP, n8n, WhatsApp ou outro efeito externo.
- NÃƒÆ’Ã‚Â£o alterar FIFO, cursor de distribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, posiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, crÃƒÆ’Ã‚Â©ditos, propriedade, pausa manual ou permissÃƒÆ’Ã‚Âµes de transferÃƒÆ’Ã‚Âªncia.
- Cada alteraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o MongoDB usa nova migraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o versionada; nÃƒÆ’Ã‚Â£o editar migraÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes aplicadas.
- Vendedor nÃƒÆ’Ã‚Â£o informa sellerId para leitura ou confirmaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o; identidade vem da sessÃƒÆ’Ã‚Â£o.
- Interface desktop com evidÃƒÆ’Ã‚Âªncia visual 1440ÃƒÆ’Ã¢â‚¬â€900, sem controles decorativos.
- ComeÃƒÆ’Ã‚Â§ar cada comportamento com teste vermelho, implementar o mÃƒÆ’Ã‚Â­nimo, executar teste verde e solicitar revisÃƒÆ’Ã‚Â£o independente.
- ApÃƒÆ’Ã‚Â³s alterar documentaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, executar powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1.

## PrÃƒÆ’Ã‚Â©requisito de governanÃƒÆ’Ã‚Â§a concluÃƒÆ’Ã‚Â­do

O commit 6c8dd82 jÃƒÆ’Ã‚Â¡ registra GOV-007, DEC-031, o desenho aprovado e o contexto mestre. As tarefas seguintes implementam somente essa regra: sem e-mail, Potencial como situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o primÃƒÆ’Ã‚Â¡ria, marcador atual reversÃƒÆ’Ã‚Â­vel, notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna, filtros e relatÃƒÆ’Ã‚Â³rios administrativos.

## Interfaces produzidas

    CommercialStatus = Literal["undefined", "potential", "negotiation", "won"]

    GET  /api/lead-notifications/new
    POST /api/lead-notifications/new/acknowledge
    GET  /api/admin/reports/lead-distribution?from=ISO-8601&to=ISO-8601

A leitura de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o retorna itens mÃƒÆ’Ã‚Â­nimos e watermark. A confirmaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o atualiza newLeadsSeenAt usando mÃƒÆ’Ã‚Â¡ximo atÃƒÆ’Ã‚Â´mico. O relatÃƒÆ’Ã‚Â³rio retorna period, bySituation e bySeller; nÃƒÆ’Ã‚Â£o retorna telefone, e-mail nem histÃƒÆ’Ã‚Â³rico.

---

### Task 1: SituaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o Potencial e marcador atual reversÃƒÆ’Ã‚Â­vel

**Files:**
- Modify: apps/api/src/gerec_api/domain/operations.py
- Modify: apps/api/src/gerec_api/routes/operations.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py
- Modify: apps/api/tests/unit/test_treatment_rules.py
- Modify: apps/api/tests/integration/test_operations_transactions.py

**Consumes:** contratos existentes de TreatmentCommand e TreatmentResult.

**Produces:** CommercialStatus inclui potential; leads.isDisqualified ÃƒÆ’Ã‚Â© exatamente o valor da tratativa mais recente, enquanto lead_treatments permanece imutÃƒÆ’Ã‚Â¡vel.

- [ ] **Step 1: Write the failing tests**

    def test_treatment_accepts_potential_status() -> None:
        result = _service().register_treatment(
            TreatmentCommand("lead-1", "Cliente demonstrou interesse", "potential", False, "potential")
        )
        assert result.commercial_status == "potential"

    def test_later_treatment_removes_current_marker_and_preserves_history() -> None:
        _service(database, seller_id).register_treatment(
            TreatmentCommand(lead_id, "Contato sem aderÃƒÆ’Ã‚Âªncia ÃƒÆ’Ã‚Â  campanha", "undefined", True, "first")
        )
        result = _service(database, seller_id).register_treatment(
            TreatmentCommand(lead_id, "Passou cotaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e seguirÃƒÆ’Ã‚Â¡ negociaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o", "negotiation", False, "second")
        )
        assert result.is_disqualified is False
        assert database["leads"].find_one({"_id": lead_id})["isDisqualified"] is False
        assert [x["isDisqualified"] for x in database["lead_treatments"].documents] == [True, False]

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q

Expected: potential is invalid and the old sticky-marker behavior conflicts with the regression.

- [ ] **Step 3: Implement the minimum**

    COMMERCIAL_STATUSES = frozenset({"undefined", "potential", "negotiation", "won"})
    CommercialStatus = Literal["undefined", "potential", "negotiation", "won"]

    update = {
        "commercialStatus": command.commercial_status,
        "isDisqualified": command.is_disqualified,
        "commentCount": comment_count,
        "lastCommentAt": now,
        "updatedAt": now,
    }

Expand the Pydantic literal and Mongo validator enum. Remove only the prior assertion that requires a later false value to remain true.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py -q

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/domain/operations.py apps/api/src/gerec_api/routes/operations.py apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py apps/api/src/gerec_api/infrastructure/mongo/operations_repository.py apps/api/tests/unit/test_treatment_rules.py apps/api/tests/integration/test_operations_transactions.py
    git commit -m "feat(api): adiciona potencial e marcador reversÃƒÆ’Ã‚Â­vel"

### Task 2: Cursor persistente e API de notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o interna

**Files:**
- Create: apps/api/src/gerec_api/domain/lead_notifications.py
- Create: apps/api/src/gerec_api/infrastructure/mongo/lead_notification_repository.py
- Create: apps/api/src/gerec_api/routes/lead_notifications.py
- Create: apps/api/src/gerec_api/infrastructure/mongo/migrations/20260914_initialize_new_lead_notification_cursor.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py
- Modify: apps/api/src/gerec_api/infrastructure/mongo/indexes.py
- Modify: apps/api/src/gerec_api/main.py
- Test: apps/api/tests/integration/test_lead_notifications.py
- Test: apps/api/tests/unit/test_migration_runner.py

**Consumes:** CurrentUser, users, leads and assignedAt from existing assignment/transfer transactions.

**Produces:** NewLeadNotification, NewLeadNotificationSnapshot, LeadNotificationService and the two protected routes.

- [ ] **Step 1: Write the failing tests**

    def test_cursor_migration_initializes_only_missing_sellers_once() -> None:
        apply(database, session=None, now=lambda: NOW)
        apply(database, session=None, now=lambda: NOW + timedelta(days=1))
        assert missing_cursor_seller["newLeadsSeenAt"] == NOW
        assert existing_cursor_seller["newLeadsSeenAt"] == EXISTING

    def test_seller_sees_only_current_leads_after_cursor_and_acknowledges() -> None:
        snapshot = service.for_seller(seller)
        assert [item.lead_id for item in snapshot.items] == [str(new_lead)]
        assert service.acknowledge(seller, snapshot.watermark) == snapshot.watermark

    def test_transfer_is_visible_to_new_owner_and_later_assignment_survives_ack() -> None:
        snapshot = service.for_seller(new_owner)
        assign_lead(new_owner, at=snapshot.watermark + timedelta(seconds=1))
        service.acknowledge(new_owner, snapshot.watermark)
        assert [item.lead_id for item in service.for_seller(new_owner).items] == [str(later_lead)]

    def test_notification_routes_deny_admin_and_other_seller() -> None:
        assert admin_client.get("/api/lead-notifications/new").status_code == 403

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py -q

Expected: modules and routes are unavailable.

- [ ] **Step 3: Implement the boundary**

    @dataclass(frozen=True)
    class NewLeadNotificationSnapshot:
        items: tuple[NewLeadNotification, ...]
        watermark: datetime

    class LeadNotificationService:
        def for_seller(self, user: CurrentUser) -> NewLeadNotificationSnapshot: ...
        def acknowledge(self, user: CurrentUser, watermark: datetime) -> datetime: ...

Repository query: current assigneeId equals authenticated seller, assignedAt is greater than newLeadsSeenAt and no later than watermark, sorted assignedAt then _id. Acknowledge uses Mongo $max. Reject invalid or future watermark. Migration initializes only absent seller cursors using injectable now; register it after 20260904 migration. Add optional date|null validator field and index (assigneeId, assignedAt) named leads_assignee_assigned_at. Wire service/router in main.py. It must not write queue, assignments, outbox or FIFO state.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py apps/api/tests/integration/test_indexes.py -q

Expected: selected tests pass, including descending concurrent acknowledgements.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/domain/lead_notifications.py apps/api/src/gerec_api/infrastructure/mongo/lead_notification_repository.py apps/api/src/gerec_api/routes/lead_notifications.py apps/api/src/gerec_api/infrastructure/mongo/migrations/20260914_initialize_new_lead_notification_cursor.py apps/api/src/gerec_api/infrastructure/mongo/migrations/runner.py apps/api/src/gerec_api/infrastructure/mongo/bootstrap.py apps/api/src/gerec_api/infrastructure/mongo/indexes.py apps/api/src/gerec_api/main.py apps/api/tests/integration/test_lead_notifications.py apps/api/tests/unit/test_migration_runner.py apps/api/tests/integration/test_indexes.py
    git commit -m "feat(api): adiciona notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas de leads"

### Task 3: Filtro, ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o e relatÃƒÆ’Ã‚Â³rio administrativo no backend

**Files:**
- Create: apps/api/src/gerec_api/routes/reports.py
- Modify: apps/api/src/gerec_api/auth/permissions.py
- Modify: apps/api/src/gerec_api/routes/dashboard.py
- Modify: apps/api/src/gerec_api/main.py
- Test: apps/api/tests/integration/test_operational_read_models.py
- Test: apps/api/tests/integration/test_reports.py

**Consumes:** Task 1 commercial status; current assigneeId and assignedAt on leads.

**Produces:** DashboardService.for_user accepts assignee_id and sort; lead_distribution is admin-only.

- [ ] **Step 1: Write the failing tests**

    def test_admin_filters_by_current_assignee_and_sorts_by_status() -> None:
        response = service.for_user(admin, assignee_id=str(sandra), sort="situation")
        assert [x["sellerName"] for x in response["leads"]["items"]] == ["Sandra", "Sandra"]
        assert [x["commercialStatus"] for x in response["leads"]["items"]] == ["negotiation", "potential"]

    def test_seller_cannot_override_scope_with_assignee_id() -> None:
        response = service.for_user(seller, assignee_id=str(other_seller), sort="situation")
        assert {x["sellerName"] for x in response["leads"]["items"]} == {"Sandra"}

    def test_report_uses_current_owner_and_transfer_assignment_date() -> None:
        report = service.lead_distribution(admin, from_at=TRANSFER_AT, to_at=TRANSFER_AT + timedelta(days=1))
        assert report["bySeller"] == [{"sellerId": str(new_owner), "sellerName": "Jessica", "count": 1}]

    def test_report_route_denies_seller() -> None:
        assert seller_client.get("/api/admin/reports/lead-distribution").status_code == 403

- [ ] **Step 2: Run red**

Run: python -m pytest apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py -q

Expected: dashboard arguments, report method and route do not exist.

- [ ] **Step 3: Implement server-side reads**

Add optional assigneeId and sort query parameters to routes/dashboard.py. In DashboardService, only administrator can compose a valid seller assignee filter; seller always receives PermissionService.scope_query(current, "leads"). sort=situation orders commercialStatus ascending, then createdAt descending and _id ascending; other sort values are rejected with 422.

Implement routes/reports.py and DashboardService.lead_distribution. Validate admin and from < to. Query assignedAt in [from, to), group current commercialStatus and assigneeId, enrich names in one users query, and serialize UTC bounds. Response includes only period, bySituation and bySeller.

- [ ] **Step 4: Run green**

Run: python -m pytest apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py apps/api/tests/integration/test_permissions.py -q

Expected: selected tests pass; seller sees neither other seller leads nor report data.

- [ ] **Step 5: Commit**

    git add apps/api/src/gerec_api/routes/reports.py apps/api/src/gerec_api/auth/permissions.py apps/api/src/gerec_api/routes/dashboard.py apps/api/src/gerec_api/main.py apps/api/tests/integration/test_operational_read_models.py apps/api/tests/integration/test_reports.py apps/api/tests/integration/test_permissions.py
    git commit -m "feat(api): filtra leads e agrega relatÃƒÆ’Ã‚Â³rios"

### Task 4: Contratos web, Potencial, destaque e controles de lista

**Files:**
- Create: apps/web/src/components/lead-list-controls.tsx
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/lib/api/client.ts
- Modify: apps/web/src/lib/dashboard/queries.ts
- Modify: apps/web/src/lib/dashboard/format.ts
- Modify: apps/web/src/components/lead-table.tsx
- Modify: apps/web/src/components/lead-treatment-modal.tsx
- Modify: apps/web/src/app/dashboard/page.tsx
- Modify: apps/web/src/app/fila/page.tsx
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/lead-table.test.tsx
- Test: apps/web/src/components/lead-treatment-modal.dom.test.tsx
- Test: apps/web/src/lib/dashboard/queries.test.ts

**Consumes:** Task 3 dashboard query parameters.

**Produces:** potential UI label, row class lead-row--awaiting-treatment and LeadListControls.

- [ ] **Step 1: Write failing tests**

    it("shows Potencial in the treatment selector", () => {
      render(<LeadTreatmentModal lead={{ ...lead, commercialStatus: "potential" }} mode="write" />);
      expect(screen.getByRole("option", { name: "Potencial" })).toBeInTheDocument();
    });

    it("highlights only leads without treatment", () => {
      render(<LeadTable role="seller" leads={[{ ...lead, commentCount: 0 }, { ...lead, id: "treated", contactName: "Tratado", commentCount: 1 }]} />);
      expect(screen.getByText(lead.contactName).closest("tr")).toHaveClass("lead-row--awaiting-treatment");
      expect(screen.getByText("Tratado").closest("tr")).not.toHaveClass("lead-row--awaiting-treatment");
    });

    it("renders the assignee filter only for admin", () => {
      render(<LeadListControls role="admin" sellers={[seller]} current={{ assigneeId: null, sort: "situation" }} />);
      expect(screen.getByLabelText("ResponsÃƒÆ’Ã‚Â¡vel")).toBeInTheDocument();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/lead-table.test.tsx src/components/lead-treatment-modal.dom.test.tsx src/lib/dashboard/queries.test.ts

Expected: potential, controls and row class are absent.

- [ ] **Step 3: Implement minimal UI**

Extend TypeScript CommercialStatus and formatter with potential/Potencial. Add option value potential in LeadTreatmentModal. In LeadTable, use class lead-row--awaiting-treatment only for commentCount === 0.

LeadListControls uses usePathname, useRouter and URLSearchParams; it preserves page, lets administrator set/remove assigneeId, and lets both roles set/remove sort=situation. Dashboard and fila pages read searchParams and pass valid values to getDashboardData. CSS uses a yellow row background, sufficient text contrast and readable hover state.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/lead-table.test.tsx src/components/lead-treatment-modal.dom.test.tsx src/lib/dashboard/queries.test.ts; npm run typecheck; npm run lint

Expected: focused tests and typecheck pass; lint has no new error.

- [ ] **Step 5: Commit**

    git add apps/web/src/components/lead-list-controls.tsx apps/web/src/lib/api/types.ts apps/web/src/lib/api/client.ts apps/web/src/lib/dashboard/queries.ts apps/web/src/lib/dashboard/format.ts apps/web/src/components/lead-table.tsx apps/web/src/components/lead-treatment-modal.tsx apps/web/src/app/dashboard/page.tsx apps/web/src/app/fila/page.tsx apps/web/src/app/globals.css apps/web/src/components/lead-table.test.tsx apps/web/src/components/lead-treatment-modal.dom.test.tsx apps/web/src/lib/dashboard/queries.test.ts
    git commit -m "feat(web): adiciona filtros e destaque de tratativa"

### Task 5: Janela web de novos leads

**Files:**
- Create: apps/web/src/lib/notifications/actions.ts
- Create: apps/web/src/lib/notifications/queries.ts
- Create: apps/web/src/components/new-leads-notification-modal.tsx
- Modify: apps/web/src/lib/api/client.ts
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/app/dashboard/page.tsx
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/new-leads-notification-modal.dom.test.tsx
- Test: apps/web/src/lib/notifications/actions.test.ts

**Consumes:** Task 2 snapshot and acknowledgement routes.

**Produces:** NewLeadsNotificationModal, displayed only to seller and acknowledged only on close.

- [ ] **Step 1: Write failing tests**

    it("acknowledges the watermark only when closing", async () => {
      render(<NewLeadsNotificationModal snapshot={snapshot} />);
      expect(acknowledgeNewLeadsAction).not.toHaveBeenCalled();
      await user.click(screen.getByRole("button", { name: "Fechar" }));
      expect(acknowledgeNewLeadsAction).toHaveBeenCalledWith(snapshot.watermark);
    });

    it("keeps dialog open after acknowledgement failure", async () => {
      vi.mocked(acknowledgeNewLeadsAction).mockResolvedValue({ ok: false, message: "NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel confirmar os novos leads." });
      render(<NewLeadsNotificationModal snapshot={snapshot} />);
      await user.keyboard("{Escape}");
      expect(screen.getByRole("alert")).toHaveTextContent("NÃƒÆ’Ã‚Â£o foi possÃƒÆ’Ã‚Â­vel confirmar os novos leads.");
      expect(screen.getByRole("dialog", { name: "Novos leads" })).toBeVisible();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/new-leads-notification-modal.dom.test.tsx src/lib/notifications/actions.test.ts

Expected: notification modules are absent.

- [ ] **Step 3: Implement query, action and modal**

queries.ts fetches GET /api/lead-notifications/new with server session cookie and cache no-store. actions.ts is a server action that reads the session, posts watermark and returns { ok, message }. The modal has role dialog, aria-modal, title, focus return, Escape and close button. It does not create mailto, tel or external links. dashboard/page.tsx queries only for seller, tolerates service unavailability without breaking the dashboard, and renders nothing for empty snapshot.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/new-leads-notification-modal.dom.test.tsx src/lib/notifications/actions.test.ts; npm run typecheck; npm run lint

Expected: tests and typecheck pass; lint has no new error.

- [ ] **Step 5: Commit**

    git add apps/web/src/lib/notifications/actions.ts apps/web/src/lib/notifications/queries.ts apps/web/src/components/new-leads-notification-modal.tsx apps/web/src/lib/api/client.ts apps/web/src/lib/api/types.ts apps/web/src/app/dashboard/page.tsx apps/web/src/app/globals.css apps/web/src/components/new-leads-notification-modal.dom.test.tsx apps/web/src/lib/notifications/actions.test.ts
    git commit -m "feat(web): exibe novos leads em janela interna"

### Task 6: PÃƒÆ’Ã‚Â¡gina administrativa de relatÃƒÆ’Ã‚Â³rios

**Files:**
- Create: apps/web/src/app/relatorios/page.tsx
- Create: apps/web/src/components/reports-dashboard.tsx
- Create: apps/web/src/lib/reports/queries.ts
- Modify: apps/web/src/components/app-shell.tsx
- Modify: apps/web/src/lib/api/types.ts
- Modify: apps/web/src/app/globals.css
- Test: apps/web/src/components/reports-dashboard.test.tsx
- Test: apps/web/src/components/app-shell.test.tsx
- Test: apps/web/src/lib/reports/queries.test.ts

**Consumes:** Task 3 lead distribution response.

**Produces:** /relatorios, admin-only navigation and two accessible bar charts.

- [ ] **Step 1: Write failing tests**

    it("renders situation and seller distributions with text equivalents", () => {
      render(<ReportsDashboard report={report} />);
      expect(screen.getByRole("heading", { name: "Por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o" })).toBeVisible();
      expect(screen.getByText("Potencial: 3")).toBeVisible();
      expect(screen.getByRole("heading", { name: "Por vendedor" })).toBeVisible();
    });

    it("shows RelatÃƒÆ’Ã‚Â³rios only to admin", () => {
      expect(renderShell(admin).getByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" })).toBeVisible();
      expect(renderShell(seller).queryByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" })).toBeNull();
    });

- [ ] **Step 2: Run red**

Run: npm run test -- src/components/reports-dashboard.test.tsx src/components/app-shell.test.tsx src/lib/reports/queries.test.ts

Expected: reports files and navigation link are absent.

- [ ] **Step 3: Implement server-rendered report page**

The route gets session and redirects seller to /dashboard. It parses all-history default, current month, last 30 days and custom from/to. queries.ts calls the administrative report endpoint with session cookie. AppShell receives /relatorios in its activePath union and renders the link only for administrator.

ReportsDashboard uses a GET form and CSS bars whose width is count / maximum ÃƒÆ’Ã¢â‚¬â€ 100. Every visual bar has visible text Name: N, and both groups have a zero-data empty state. Do not add a chart dependency.

- [ ] **Step 4: Run green**

Run: npm run test -- src/components/reports-dashboard.test.tsx src/components/app-shell.test.tsx src/lib/reports/queries.test.ts; npm run typecheck; npm run lint

Expected: focused suite passes and seller has no report navigation.

- [ ] **Step 5: Commit**

    git add apps/web/src/app/relatorios/page.tsx apps/web/src/components/reports-dashboard.tsx apps/web/src/lib/reports/queries.ts apps/web/src/components/app-shell.tsx apps/web/src/lib/api/types.ts apps/web/src/app/globals.css apps/web/src/components/reports-dashboard.test.tsx apps/web/src/components/app-shell.test.tsx apps/web/src/lib/reports/queries.test.ts
    git commit -m "feat(web): adiciona relatÃƒÆ’Ã‚Â³rios administrativos"

### Task 7: E2E, capturas e evidÃƒÆ’Ã‚Âªncias

**Files:**
- Create or Modify: apps/web/e2e/operacao-notificacoes-relatorios.spec.ts
- Create: docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md
- Modify: docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md only through its generator

**Consumes:** Tasks 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6.

**Produces:** acceptance evidence, screenshots 1440ÃƒÆ’Ã¢â‚¬â€900 and final quality gates.

- [ ] **Step 1: Write E2E acceptance tests**

    test("seller sees new lead, records Potencial and clears current marker", async ({ page }) => {
      await signInAs(page, "sandra@wtgseguros.com.br");
      await expect(page.getByRole("dialog", { name: "Novos leads" })).toBeVisible();
      await page.getByRole("button", { name: "Fechar" }).click();
      await page.getByRole("button", { name: /Registrar tratativa/ }).first().click();
      await page.getByLabel("SituaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o comercial").selectOption("potential");
      await page.getByLabel("Marcar como Desqualificado").uncheck();
      await page.getByLabel("ComentÃƒÆ’Ã‚Â¡rio").fill("Cliente pediu nova proposta comercial");
      await page.getByRole("button", { name: "Salvar tratativa" }).click();
      await expect(page.getByText("Desqualificado")).not.toBeVisible();
    });

    test("admin filters leads and views reports", async ({ page }) => {
      await signInAs(page, "yago@wtgseguros.com.br");
      await page.getByLabel("ResponsÃƒÆ’Ã‚Â¡vel").selectOption({ label: "Sandra" });
      await page.getByRole("link", { name: "RelatÃƒÆ’Ã‚Â³rios" }).click();
      await expect(page.getByRole("heading", { name: "Por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o" })).toBeVisible();
    });

- [ ] **Step 2: Run the E2E test and correct only fixture/selector gaps**

Run: npm run test:e2e -- operacao-notificacoes-relatorios.spec.ts

Expected: test passes after Tasks 1ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“6. Preserve authorization assertions; do not weaken them to make a fixture pass.

- [ ] **Step 3: Capture visual evidence**

Capture seller-new-leads-1440x900.png, admin-lead-filter-1440x900.png and admin-reports-1440x900.png after asserted visible states. Use a 1440ÃƒÆ’Ã¢â‚¬â€900 viewport and agent-browser or the existing Playwright screenshot fixture.

- [ ] **Step 4: Run all gates**

    python -m pytest apps/api/tests -q
    npm run test
    npm run lint
    npm run typecheck
    npm run build
    npm run test:e2e
    git diff --check

Expected: no failure, no lint error, successful build and E2E. Record any pre-existing warning separately.

- [ ] **Step 5: Record evidence and regenerate context**

Create the evidence table with actual command totals, E2E result, screenshots and authorization result. Then run:

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/generate-master-context.ps1
    git diff --check

- [ ] **Step 6: Commit**

    git add apps/web/e2e/operacao-notificacoes-relatorios.spec.ts docs/evidencias/2026-09-14-notificacoes-internas-tratativas-relatorios.md docs/CONTEXTO_MESTRE_GERENCIADOR_DE_LEADS.md
    git commit -m "test: valida notificaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Âµes internas e relatÃƒÆ’Ã‚Â³rios"

## Plan self-review

| Requisito aprovado | Tarefa |
| --- | --- |
| Potencial | 1, 4 |
| Desqualificado reflete a ÃƒÆ’Ã‚Âºltima tratativa, com histÃƒÆ’Ã‚Â³rico preservado | 1, 7 |
| Destaque amarelo sem efeito operacional | 4, 7 |
| Cursor persistente, atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o/transferÃƒÆ’Ã‚Âªncia futura e sem e-mail | 2, 5, 7 |
| Filtro administrativo e ordenaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o para ambos | 3, 4, 7 |
| RelatÃƒÆ’Ã‚Â³rios admin por situaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o/proprietÃƒÆ’Ã‚Â¡rio atual e perÃƒÆ’Ã‚Â­odo por atribuiÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o atual | 3, 6, 7 |
| AutorizaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o, concorrÃƒÆ’Ã‚Âªncia, FIFO e validaÃƒÆ’Ã‚Â§ÃƒÆ’Ã‚Â£o visual | 2, 3, 5, 7 |

A ordem dos contratos ÃƒÆ’Ã‚Â© consistente: Task 1 introduz potential; Task 2 produz a API que Task 5 consome; Task 3 produz a API que Task 6 consome. Nenhuma tarefa cria e-mail ou modifica o cursor FIFO.
