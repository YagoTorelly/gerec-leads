import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { applySubmissionToLead, commentCountsAfterSubmission, LeadTable } from "./lead-table";
import { LeadTreatmentModal, validateTreatmentDraft } from "./lead-treatment-modal";

const lead = {
  id: "lead-1",
  contactName: "Débora Souza",
  sellerName: "Renato",
  companyName: "Empresa da Débora",
  campaignName: "Campanha WTG",
  phoneDisplay: "(11) 98830-8029",
  email: "debora@example.com",
  commercialStatus: "negotiation" as const,
  isDisqualified: false,
  commentCount: 2,
  assignedAt: "2026-08-28T16:03:04.876Z",
  feedbackDueAt: "2026-08-29T16:03:04.876Z",
  lastUpdatedAt: "2026-08-28T16:03:04.876Z",
};

describe("tabela de leads e tratativa", () => {
  it("mostra responsável somente na visão administrativa", () => {
    const admin = renderToStaticMarkup(createElement(LeadTable, { leads: [lead], role: "admin" }));
    const seller = renderToStaticMarkup(
      createElement(LeadTable, { leads: [lead], role: "seller" }),
    );

    expect(admin).toContain("Responsável");
    expect(admin).toContain("Renato");
    expect(admin).toContain("Empresa da Débora");
    expect(admin).toContain("Campanha WTG");
    expect(admin).toContain("2 comentários");
    expect(admin).not.toContain("Registrar tratativa");
    expect(seller).not.toContain("Responsável");
    expect(seller).toContain("Registrar tratativa");
  });

  it("exibe somente os campos comerciais e o histórico em modo leitura", () => {
    const markup = renderToStaticMarkup(
      createElement(LeadTreatmentModal, {
        lead,
        mode: "read",
        defaultOpen: true,
        treatments: [
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Primeiro contato por telefone.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            assignedAt: "2026-08-28T15:30:00.000Z",
            createdAt: "2026-08-28T16:03:04.876Z",
            lastUpdatedAt: "2026-08-28T16:03:04.876Z",
          },
        ],
      }),
    );

    expect(markup).toContain("Histórico de tratativas");
    expect(markup).toContain("Primeiro contato por telefone.");
    expect(markup).not.toContain("Salvar tratativa");
    expect(markup).not.toContain("<textarea");
  });

  it("oferece as três situações, marcador adicional e bloqueia comentário curto", () => {
    const markup = renderToStaticMarkup(
      createElement(LeadTreatmentModal, {
        lead,
        mode: "write",
        treatments: [],
        defaultOpen: true,
      }),
    );

    expect(markup).toContain("Indefinido");
    expect(markup).toContain("Negociação");
    expect(markup).toContain("Ganho");
    expect(markup).toContain("Desqualificado");
    expect(markup).toContain("Salvar tratativa");
    expect(
      validateTreatmentDraft({
        comment: "curto",
        commercialStatus: "undefined",
        isDisqualified: false,
      }),
    ).toEqual({
      ok: false,
      message: "Escreva um comentário com ao menos 6 caracteres.",
    });
  });

  it("atualiza o contador exibido com o total devolvido pela API", () => {
    expect(
      commentCountsAfterSubmission(
        { "outro-lead": 1 },
        {
          leadId: "lead-1",
          treatmentId: "treatment-1",
          status: "created",
          commercialStatus: "won",
          isDisqualified: false,
          commentCount: 3,
          reminderAt: null,
          dueAt: null,
          lastUpdatedAt: "2026-08-29T15:00:00.000Z",
        },
      ),
    ).toEqual({ "outro-lead": 1, "lead-1": 3 });
  });

  it("reflete a tratativa salva na própria linha do lead", () => {
    expect(
      applySubmissionToLead(lead, {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "won",
        isDisqualified: true,
        commentCount: 3,
        reminderAt: null,
        dueAt: null,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      }),
    ).toMatchObject({
      commercialStatus: "won",
      isDisqualified: true,
      commentCount: 3,
      feedbackDueAt: null,
    });
  });

  it("exibe a última atualização persistida mesmo quando o relógio do navegador diverge", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2030-01-01T00:00:00.000Z"));
    try {
      const updatedLead = applySubmissionToLead(lead, {
        leadId: "lead-1",
        treatmentId: "treatment-1",
        status: "created",
        commercialStatus: "negotiation",
        isDisqualified: false,
        commentCount: 3,
        reminderAt: null,
        dueAt: null,
        lastUpdatedAt: "2026-08-29T15:00:00.000Z",
      });
      const markup = renderToStaticMarkup(
        createElement(LeadTable, { leads: [updatedLead], role: "seller" }),
      );

      expect(markup).toContain("29/08/2026, 12:00");
      expect(markup).not.toContain("31/12/2029");
    } finally {
      vi.useRealTimers();
    }
  });
});
