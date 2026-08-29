import { renderToStaticMarkup } from "react-dom/server";
import { beforeEach, describe, expect, it, vi } from "vitest";

const { getDashboardData, getSessionContext, redirect } = vi.hoisted(() => ({
  getDashboardData: vi.fn(),
  getSessionContext: vi.fn(),
  redirect: vi.fn(),
}));

vi.mock("next/navigation", () => ({ redirect }));
vi.mock("../lib/auth/session", () => ({ getSessionContext }));
vi.mock("../lib/dashboard/queries", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../lib/dashboard/queries")>()),
  getDashboardData,
}));

import DashboardPage from "./dashboard/page";
import HistoryPage from "./historico/page";

const sellerSession = {
  status: "authenticated" as const,
  sessionToken: "seller-session",
  profile: {
    id: "seller-1",
    userId: "seller-1",
    fullName: "Jessica",
    email: "jessica@wtgseguros.com.br",
    role: "seller" as const,
  },
};

describe("proteção das rotas operacionais", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    redirect.mockImplementation((target: string) => { throw new Error(`REDIRECT:${target}`); });
  });

  it("redireciona vendedor que tenta abrir o histórico global por URL", async () => {
    getSessionContext.mockResolvedValue(sellerSession);

    await expect(HistoryPage({ searchParams: Promise.resolve({}) })).rejects.toThrow("REDIRECT:/dashboard");
    expect(redirect).toHaveBeenCalledWith("/dashboard");
    expect(getDashboardData).not.toHaveBeenCalled();
  });

  it("renderiza um estado seguro quando a API não disponibiliza o dashboard", async () => {
    getSessionContext.mockResolvedValue({
      ...sellerSession,
      profile: { ...sellerSession.profile, role: "admin" as const },
    });
    getDashboardData.mockRejectedValue(new Error("API indisponível"));

    const markup = renderToStaticMarkup(await DashboardPage({ searchParams: Promise.resolve({}) }));

    expect(markup).toContain("Não foi possível carregar a visão geral.");
    expect(markup).toContain("Tente atualizar a página em alguns instantes.");
  });
});
