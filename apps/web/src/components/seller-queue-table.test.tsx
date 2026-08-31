import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SellerQueueTable } from "./seller-queue-table";

describe("SellerQueueTable", () => {
  it("mostra a posição e disponibilidade do vendedor sem dados globais da fila", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerQueueTable, {
        queue: { position: 3, availability: "active", skipBalance: 0 },
        leads: [],
      }),
    );

    expect(markup).toContain("Minha fila");
    expect(markup).toContain("Posição 3");
    expect(markup).toContain("Disponível para novas atribuições");
    expect(markup).not.toContain("Renato");
    expect(markup).not.toContain("Jessica");
  });

  it("informa quando a posição não está disponível", () => {
    const markup = renderToStaticMarkup(
      createElement(SellerQueueTable, {
        queue: { position: null, availability: "blocked_overdue", skipBalance: 2 },
        leads: [],
      }),
    );

    expect(markup).toContain("Posição não informada");
    expect(markup).toContain("Bloqueado por atraso");
    expect(markup).toContain("Saldo de pulos: 2");
  });
});
