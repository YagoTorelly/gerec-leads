import { describe, expect, it } from "vitest";

import {
  buildHistoryView,
  buildQueueView,
  type HistorySourceAttempt,
  type HistorySourceAssignment,
  type HistorySourceFeedback,
  type HistorySourceLead,
  type HistorySourceProfile,
  type HistorySourceQualification,
  type HistorySourceSale,
  type QueueSourceEntry,
} from "./operations-view";

const adminProfile = {
  userId: "admin-1",
  fullName: "Yago Admin",
  email: "admin@gerec.local",
  role: "admin" as const,
};

const queueEntries: QueueSourceEntry[] = [
  {
    sellerId: "seller-1",
    sellerName: "Renato",
    sellerEmail: "renato@gerec.local",
    position: 1,
    isPaused: false,
    skipBalance: 0,
  },
  {
    sellerId: "seller-2",
    sellerName: "Sandra",
    sellerEmail: "sandra@gerec.local",
    position: 2,
    isPaused: true,
    skipBalance: 2,
  },
];

const leads: HistorySourceLead[] = [
  {
    id: 101,
    contactName: "Marina Costa",
    companyName: "Meta Servicos Integrados",
    sellerId: "seller-1",
    sellerName: "Renato",
    stage: "overdue",
    feedbackDueAt: "2026-08-26T10:00:00.000Z",
  },
  {
    id: 102,
    contactName: "Rafael Nunes",
    companyName: "Rafael Nunes Studio",
    sellerId: "seller-2",
    sellerName: "Sandra",
    stage: "today",
    feedbackDueAt: "2026-08-26T21:00:00.000Z",
  },
];

describe("buildQueueView", () => {
  it("resume a fila por vendedor com contagens operacionais", () => {
    const data = buildQueueView({
      profile: adminProfile,
      leads,
      queueEntries,
      source: "supabase",
      nextSellerId: "seller-2",
      now: new Date("2026-08-26T12:00:00.000Z"),
    });

    expect(data.entries).toHaveLength(2);
    expect(data.entries[0]).toMatchObject({
      sellerName: "Renato",
      activeLeads: 1,
      overdueLeads: 1,
      isNextInLine: false,
      position: 1,
    });
    expect(data.entries[1]).toMatchObject({
      sellerName: "Sandra",
      dueTodayLeads: 1,
      isPaused: true,
      isNextInLine: true,
      skipBalance: 2,
    });
  });
});

describe("buildHistoryView", () => {
  it("monta a timeline unificada em ordem decrescente", () => {
    const profiles: HistorySourceProfile[] = [
      { userId: "seller-1", fullName: "Renato" },
      { userId: "seller-2", fullName: "Sandra" },
    ];
    const assignments: HistorySourceAssignment[] = [
      {
        id: 1,
        leadId: 101,
        sellerId: "seller-1",
        assignmentType: "normal",
        startedAt: "2026-08-25T12:00:00.000Z",
        reason: "Distribuicao inicial",
      },
    ];
    const feedbacks: HistorySourceFeedback[] = [
      {
        id: 10,
        leadId: 101,
        sellerId: "seller-1",
        comment: "Primeiro retorno realizado com interesse.",
        createdAt: "2026-08-26T11:00:00.000Z",
      },
    ];
    const attempts: HistorySourceAttempt[] = [
      {
        id: 11,
        leadId: 101,
        sellerId: "seller-1",
        comment: "Tentativa por WhatsApp sem resposta.",
        createdAt: "2026-08-26T09:00:00.000Z",
        businessDate: "2026-08-26",
      },
    ];
    const qualifications: HistorySourceQualification[] = [
      {
        id: 12,
        leadId: 102,
        actorId: "seller-2",
        outcome: "qualified_follow_up",
        reason: null,
        comment: "Lead aquecido para proposta.",
        createdAt: "2026-08-26T08:00:00.000Z",
      },
    ];
    const sales: HistorySourceSale[] = [
      {
        id: 13,
        leadId: 102,
        sellerId: "seller-2",
        comment: "Contrato fechado no mesmo dia.",
        wonAt: "2026-08-26T12:30:00.000Z",
      },
    ];

    const data = buildHistoryView({
      profile: adminProfile,
      leads,
      profiles,
      assignments,
      feedbacks,
      attempts,
      qualifications,
      sales,
      source: "supabase",
      now: new Date("2026-08-26T13:00:00.000Z"),
    });

    expect(data.items.map((item) => item.type)).toEqual([
      "sale",
      "feedback",
      "attempt",
      "qualification",
      "assignment",
    ]);
    expect(data.items[0]).toMatchObject({
      leadId: 102,
      sellerName: "Sandra",
      headline: "Negocio ganho",
      tone: "green",
    });
    expect(data.items[1]).toMatchObject({
      leadId: 101,
      sellerName: "Renato",
      type: "feedback",
    });
  });
});
