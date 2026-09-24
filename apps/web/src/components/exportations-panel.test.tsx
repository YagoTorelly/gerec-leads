// @vitest-environment jsdom

import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import type { Page, ExportationHistoryItem } from "../lib/api/types";
import { ExportationsPanel } from "./exportations-panel";

const history: Page<ExportationHistoryItem> = {
  items: [
    {
      createdAt: "2026-09-22T15:30:00.000Z",
      administratorName: "Yago",
      leadCount: 12,
      filters: {},
      status: "success",
    },
    {
      createdAt: "2026-09-22T16:45:00.000Z",
      administratorName: "Andr\u00e9",
      leadCount: 0,
      filters: { situation: "potential" },
      status: "error",
    },
  ],
  page: 1,
  pageSize: 50,
  total: 2,
};

afterEach(cleanup);

describe("ExportationsPanel", () => {
  it("oferece somente o Excel de leads e mostra todo o hist\u00f3rico aprovado", () => {
    const screen = render(<ExportationsPanel history={history} />);

    const download = screen.getByRole("button", { name: "Exportar leads em Excel" });
    expect(screen.queryByRole("link", { name: /hist\u00f3rico/i })).toBeNull();
    expect(screen.getByText("22/09/2026, 12:30")).toBeTruthy();
    expect(screen.getByText("Yago")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByText("Todos os leads")).toBeTruthy();
    expect(screen.getByText("Situa\u00e7\u00e3o: potential")).toBeTruthy();
    expect(screen.getByText("Conclu\u00edda")).toBeTruthy();
    expect(screen.getByText("Falhou")).toBeTruthy();
  });

  it("mant\u00e9 o painel recuper\u00e1vel quando o hist\u00f3rico falha", () => {
    const screen = render(
      <ExportationsPanel
        history={null}
        error="N\u00e3o foi poss\u00edvel carregar o hist\u00f3rico de exporta\u00e7\u00f5es."
        retryHref="/exportacoes?page=2"
      />,
    );

    expect(screen.getByRole("button", { name: "Exportar leads em Excel" })).toBeTruthy();
    const retry = screen.getByRole("link", { name: "Tentar novamente" });
    expect(retry.getAttribute("href")).toBe("/exportacoes?page=2");
    expect(
      screen.getByRole("region", { name: "Hist\u00f3rico de exporta\u00e7\u00f5es" }),
    ).toBeTruthy();
  });

  it("mostra um estado vazio sem inventar exporta\u00e7\u00f5es", () => {
    const screen = render(
      <ExportationsPanel history={{ items: [], page: 1, pageSize: 50, total: 0 }} />,
    );
    expect(screen.getByText("Nenhuma exporta\u00e7\u00e3o registrada.")).toBeTruthy();
  });
});
