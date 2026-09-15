import { describe, expect, it, vi } from "vitest";

const { getLeadDistributionReport, getSessionContext, redirect } = vi.hoisted(() => ({
  getLeadDistributionReport: vi.fn(),
  getSessionContext: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../../lib/reports/queries", () => ({
  getLeadDistributionReport,
  reportPeriod: vi.fn(),
}));

import ReportsPage from "./page";

describe("ReportsPage", () => {
  it("redireciona vendedor para o dashboard antes de consultar o relat\u00f3rio", async () => {
    getSessionContext.mockResolvedValue({
      status: "authenticated",
      sessionToken: "seller-session",
      profile: {
        id: "seller-1",
        userId: "seller-1",
        fullName: "Jessica",
        email: "jessica@wtgseguros.com.br",
        role: "seller",
      },
    });
    redirect.mockImplementation((path: string) => {
      throw new Error(`REDIRECT:${path}`);
    });

    await expect(ReportsPage({ searchParams: Promise.resolve({}) })).rejects.toThrow("REDIRECT:/dashboard");
    expect(redirect).toHaveBeenCalledWith("/dashboard");
    expect(getLeadDistributionReport).not.toHaveBeenCalled();
  });
});
