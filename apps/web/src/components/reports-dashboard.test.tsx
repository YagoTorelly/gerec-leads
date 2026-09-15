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
  it("renderiza distribui\u00e7\u00f5es por situa\u00e7\u00e3o e vendedor com equivalentes textuais", () => {
    render(<ReportsDashboard report={report} period="all" />);

    expect(screen.getByRole("heading", { name: "Por situa\u00e7\u00e3o" })).toBeTruthy();
    expect(screen.getByText("Potencial: 3")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Por vendedor" })).toBeTruthy();
    expect(screen.getByText("Jessica: 4")).toBeTruthy();
  });
});
