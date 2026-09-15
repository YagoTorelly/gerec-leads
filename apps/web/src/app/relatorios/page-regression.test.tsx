import { beforeEach, describe, expect, it, vi } from "vitest";

const { AppShell, ReportsDashboard, getLeadDistributionReport, getSessionContext, isReportPeriod, reportPeriod } = vi.hoisted(() => ({
  AppShell: vi.fn(),
  ReportsDashboard: vi.fn(),
  getLeadDistributionReport: vi.fn(),
  getSessionContext: vi.fn(),
  isReportPeriod: vi.fn((period) => "fromAt" in period),
  reportPeriod: vi.fn(),
}));

vi.mock("../../components/app-shell", () => ({ AppShell }));
vi.mock("../../components/reports-dashboard", () => ({ ReportsDashboard }));
vi.mock("../../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../../lib/reports/queries", () => ({ getLeadDistributionReport, isReportPeriod, reportPeriod }));

import ReportsPage from "./page";

describe("recuperação da página de relatórios", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "admin-session",
      profile: { id: "admin-1", userId: "admin-1", fullName: "Yago", email: "yago@wtg.test", role: "admin" },
    });
    reportPeriod.mockReturnValue({
      key: "custom",
      fromAt: "2026-09-01T03:00:00.000Z",
      toAt: "2026-09-15T03:00:00.000Z",
    });
  });

  it("preserva shell e nova tentativa quando a consulta falha", async () => {
    getLeadDistributionReport.mockRejectedValue(new Error("indisponível"));

    const page = await ReportsPage({ searchParams: Promise.resolve({ period: "custom" }) });

    expect(page.type).toBe(AppShell);
    expect(page.props.children.type).toBe(ReportsDashboard);
    expect(page.props.children.props).toMatchObject({
      report: null,
      interval: {
        from: "2026-09-01T03:00:00.000Z",
        to: "2026-09-15T03:00:00.000Z",
      },
      error: "Não foi possível carregar os relatórios. Tente novamente.",
    });
  });
});
