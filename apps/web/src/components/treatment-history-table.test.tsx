import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TreatmentHistoryTable } from "./treatment-history-table";

describe("TreatmentHistoryTable", () => {
  it("agrupa a conversa por lead com vendedor, início, última atualização e comentários", () => {
    const markup = renderToStaticMarkup(
      createElement(TreatmentHistoryTable, {
        treatments: [
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Primeiro contato realizado por telefone.",
            commercialStatus: "won",
            isDisqualified: true,
            assignedAt: "2026-08-28T15:30:00.000Z",
            lastUpdatedAt: "2026-08-28T16:03:04.876Z",
            createdAt: "2026-08-28T16:03:04.876Z",
          },
          {
            leadId: "lead-1",
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Cliente pediu retorno com proposta.",
            commercialStatus: "negotiation",
            isDisqualified: false,
            assignedAt: "2026-08-28T15:30:00.000Z",
            lastUpdatedAt: "2026-08-28T16:10:00.000Z",
            createdAt: "2026-08-28T15:40:00.000Z",
          },
        ],
      }),
    );

    expect(markup).toContain("Tratativas");
    expect(markup).toContain("Débora Souza");
    expect(markup).toContain("Renato");
    expect(markup).toContain("Início");
    expect(markup).toContain("Última atualização");
    expect(markup).toContain("Primeiro contato realizado por telefone.");
    expect(markup).toContain("Cliente pediu retorno com proposta.");
    expect(markup).toContain("Ganho");
    expect(markup).toContain("Desqualificado");
    expect(markup).toContain("28/08/2026");
    expect(markup).not.toContain("Atribuições");
  });
});
