import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TreatmentHistoryTable } from "./treatment-history-table";

describe("TreatmentHistoryTable", () => {
  it("mostra a tratativa, e não a lista legada de atribuições", () => {
    const markup = renderToStaticMarkup(
      createElement(TreatmentHistoryTable, {
        treatments: [
          {
            leadName: "Débora Souza",
            sellerName: "Renato",
            comment: "Primeiro contato realizado por telefone.",
            commercialStatus: "won",
            isDisqualified: true,
            createdAt: "2026-08-28T16:03:04.876Z",
          },
        ],
      }),
    );

    expect(markup).toContain("Tratativas");
    expect(markup).toContain("Lead");
    expect(markup).toContain("Vendedor");
    expect(markup).toContain("Comentário");
    expect(markup).toContain("Primeiro contato realizado por telefone.");
    expect(markup).toContain("Ganho");
    expect(markup).toContain("Desqualificado");
    expect(markup).toContain("28/08/2026");
    expect(markup).not.toContain("Atribuições");
  });
});
