import { describe, expect, it } from "vitest";

import { buildDashboardData } from "./build-dashboard-data";

describe("buildDashboardData", () => {
  it("monta resumo, fila, historico e usuarios a partir dos registros retornados pela RLS", () => {
    const data = buildDashboardData({
      leads: [
        {
          id: 1,
          company_id: 10,
          campaign_id: 20,
          current_assignee_id: "seller-1",
          assignment_status: "assigned",
          qualification_status: "pending",
          conversion_status: "active",
          source_entered_at: "2026-08-26T11:00:00.000Z",
          feedback_due_at: "2026-08-26T18:00:00.000Z",
          updated_at: "2026-08-26T11:10:00.000Z",
        },
      ],
      profiles: [
        { user_id: "seller-1", full_name: "Renato", email: "renato@gerec.local", role: "seller" },
        { user_id: "seller-2", full_name: "Sandra", email: "sandra@gerec.local", role: "seller" },
      ],
      companies: [{ id: 10, legal_name: "Empresa A", document_display: "12.000.000/0001-00" }],
      campaigns: [{ id: 20, display_name: "Campanha" }],
      sourceRecords: [
        {
          lead_id: 1,
          mock_has_cnpj_or_mei: "sim",
          full_name: "Cliente A",
          phone: "(11) 90000-0000",
          email: "cliente@exemplo.com",
        },
      ],
      queueEntries: [
        { seller_id: "seller-1", position: 1, is_paused: false },
        { seller_id: "seller-2", position: 2, is_paused: true },
      ],
      skipBalances: [
        { seller_id: "seller-1", balance: 0 },
        { seller_id: "seller-2", balance: 2 },
      ],
      attempts: [
        {
          id: 1001,
          lead_id: 1,
          seller_id: "seller-1",
          comment: "Primeiro contato",
          created_at: "2026-08-26T10:40:00.000Z",
        },
      ],
      feedbacks: [
        {
          id: 2001,
          lead_id: 1,
          seller_id: "seller-1",
          comment: "Cliente pediu retorno amanha",
          created_at: "2026-08-26T09:30:00.000Z",
        },
      ],
      qualificationEvents: [],
      sales: [],
      now: new Date("2026-08-26T12:00:00.000Z"),
      source: "supabase",
    });

    expect(data.summary.total).toBe(1);
    expect(data.summary.feedbacksToday).toBe(1);
    expect(data.leads[0]).toMatchObject({
      contactName: "Cliente A",
      sellerName: "Renato",
      attemptsCount: 1,
      stage: "today",
    });
    expect(data.queue).toEqual([
      expect.objectContaining({
        sellerName: "Renato",
        position: 1,
        activeLeads: 1,
        overdueLeads: 0,
        isPaused: false,
        skipBalance: 0,
      }),
      expect.objectContaining({
        sellerName: "Sandra",
        position: 2,
        activeLeads: 0,
        overdueLeads: 0,
        isPaused: true,
        skipBalance: 2,
      }),
    ]);
    expect(data.history[0]).toMatchObject({
      eventType: "attempt",
      sellerName: "Renato",
      leadId: 1,
    });
    expect(data.users).toEqual([
      expect.objectContaining({
        fullName: "Renato",
        role: "seller",
        activeLeads: 1,
        queuePosition: 1,
      }),
      expect.objectContaining({
        fullName: "Sandra",
        role: "seller",
        activeLeads: 0,
        queuePosition: 2,
      }),
    ]);
  });
});
