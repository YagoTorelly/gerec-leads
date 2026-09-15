// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ReportsDashboard } from "./reports-dashboard";

afterEach(cleanup);

describe("regressões do painel de relatórios", () => {
  it("mantém datas e contexto do intervalo personalizado no formulário", () => {
    render(
      <ReportsDashboard
        report={{
          period: { from: "2026-09-01T03:00:00.000Z", to: "2026-09-15T03:00:00.000Z" },
          bySituation: [],
          bySeller: [],
        }}
        period="custom"
      />,
    );

    expect(screen.getByLabelText("De").getAttribute("value")).toBe("2026-09-01");
    expect(screen.getByLabelText("Até").getAttribute("value")).toBe("2026-09-15");
    expect(screen.getByText(/baseado na atribuição atual/i)).toBeTruthy();
  });

  it("mantem datas personalizadas quando a consulta falha", () => {
    render(
      <ReportsDashboard
        report={null}
        period="custom"
        error="Erro ao carregar relatorio."
        interval={{
          from: "2026-09-01T03:00:00.000Z",
          to: "2026-09-15T03:00:00.000Z",
        }}
      />,
    );

    expect(screen.getByLabelText("De").getAttribute("value")).toBe("2026-09-01");
    expect(screen.getByRole("alert")).toBeTruthy();
  });
});
