import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Pagination } from "./pagination";

describe("Pagination", () => {
  it("usa botões acessíveis, mantém a query e desabilita limites", () => {
    const markup = renderToStaticMarkup(
      createElement(Pagination, {
        href: "/historico",
        page: { items: [], page: 1, pageSize: 10, total: 20 },
        searchParams: { campaign: "campanha-1", page: "1" },
      }),
    );

    expect(markup).toMatch(
      /<button[^>]*disabled=""[^>]*aria-label="Página anterior"[^>]*name="page"/,
    );
    expect(markup).toMatch(/<button[^>]*value="2"[^>]*aria-label="Próxima página"[^>]*name="page"/);
    expect(markup).toContain('name="campaign" value="campanha-1"');
    expect(markup).toContain("Página 1 de 2");
    expect(markup).not.toContain("AnteriorPágina");
  });

  it("desabilita a próxima página no fim da coleção", () => {
    const markup = renderToStaticMarkup(
      createElement(Pagination, {
        href: "/historico",
        page: { items: [], page: 2, pageSize: 10, total: 20 },
      }),
    );

    expect(markup).toMatch(
      /<button[^>]*value="2"[^>]*disabled=""[^>]*aria-label="Próxima página"[^>]*name="page"/,
    );
  });
});
