// @vitest-environment jsdom

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ReportsDashboard } from "./reports-dashboard";

const report = {
  period: { from: "2026-09-01T00:00:00.000Z", to: "2026-09-15T00:00:00.000Z" },
  bySituation: [
    { commercialStatus: "potential" as const, count: 3 },
    { commercialStatus: "won" as const, count: 1 },
  ],
  bySeller: [{ sellerId: "seller-1", sellerName: "Jessica", count: 4 }],
};

afterEach(cleanup);

describe("ReportsDashboard", () => {
  it("renderiza os dois gr\u00e1ficos em linhas completas com colunas verticais e equivalentes textuais", () => {
    const { container } = render(<ReportsDashboard report={report} period="all" />);

    expect(screen.getByRole("heading", { name: "Por situa\u00e7\u00e3o" })).toBeTruthy();
    expect(screen.getByText("Potencial: 3")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Por vendedor" })).toBeTruthy();
    expect(screen.getByText("Jessica: 4")).toBeTruthy();

    expect(container.querySelector(".reports-dashboard--stacked")).toBeTruthy();
    expect(container.querySelectorAll(".report-card--full")).toHaveLength(2);
    expect(container.querySelectorAll(".report-columns")).toHaveLength(2);
    expect(container.querySelectorAll(".report-column")).toHaveLength(3);

    const bars = container.querySelectorAll<HTMLElement>(".report-column__bar");
    expect(bars[0]?.style.height).toBe("100%");
    expect(bars[1]?.style.height).toBe("33.33333333333333%");
    expect(bars[2]?.style.height).toBe("100%");
  });

  it("mostra estado vazio para ambas as distribui\u00e7\u00f5es", () => {
    render(<ReportsDashboard report={{ ...report, bySituation: [], bySeller: [] }} period="all" />);

    expect(screen.getAllByText("Nenhum dado para o per\u00edodo selecionado.")).toHaveLength(2);
  });
});
