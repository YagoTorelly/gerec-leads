import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { QueueTable } from "./queue-table";

describe("QueueTable", () => {
  it("exibe a ordem operacional atual em vez da posição fixa do cadastro", () => {
    const markup = renderToStaticMarkup(
      createElement(QueueTable, {
        queue: {
          cursorSellerName: "Renato",
          nextSellerName: "Jessica",
          total: 3,
          items: [
            {
              sellerName: "Jessica",
              position: 3,
              availability: "active",
              reason: null,
              skipBalance: 0,
            },
            {
              sellerName: "Nelma",
              position: 4,
              availability: "active",
              reason: null,
              skipBalance: 0,
            },
            {
              sellerName: "Renato",
              position: 1,
              availability: "paused",
              reason: "Pausado manualmente",
              skipBalance: 1,
            },
          ],
        },
      }),
    );

    expect(markup).toContain("Cursor atual");
    expect(markup).toContain("Renato");
    expect(markup).toContain("Próximo elegível");
    expect(markup).toContain("Jessica");
    expect(markup).toContain("Ordem atual");
    expect(markup).toContain("Posição base");
    expect(markup).toContain("<td>1</td>");
    expect(markup).toContain("<td>3</td>");
    expect(markup).not.toContain("Bloqueado por atraso");
    expect(markup).toContain("Pausado");
    expect(markup).toContain("Créditos de pulo");
  });
});
